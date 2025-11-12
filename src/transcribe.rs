use crate::config::Config;
use crate::error::{ListenError, Result};
use whisper_rs::{FullParams, SamplingStrategy, WhisperContext, WhisperContextParameters};
use std::path::Path;

pub async fn transcribe_file(file_path: &str, config: &Config) -> Result<()> {
    if !Path::new(file_path).exists() {
        return Err(ListenError::File(std::io::Error::new(
            std::io::ErrorKind::NotFound,
            format!("File not found: {}", file_path),
        )));
    }

    if !config.quiet {
        println!("Loading audio from: {}", file_path);
    }

    // Load audio file and convert to f32 samples
    let audio_data = load_audio_file(file_path)?;

    let transcription = transcribe_buffer(&audio_data, config).await?;

    output_result(&transcription, config)?;

    Ok(())
}

pub async fn transcribe_buffer(samples: &[f32], config: &Config) -> Result<String> {
    if config.verbose {
        println!("[DEBUG] Loading whisper model: {}", config.model);
    }

    // Load whisper model
    let model_path = get_model_path(&config.model)?;

    let ctx = WhisperContext::new_with_params(
        &model_path,
        WhisperContextParameters::default(),
    )
    .map_err(|e| ListenError::Transcription(format!("Failed to load model: {:?}", e)))?;

    if config.verbose {
        println!("[DEBUG] Model loaded, transcribing {} samples", samples.len());
    }

    // Create parameters
    let mut params = FullParams::new(SamplingStrategy::Greedy { best_of: 1 });

    // Set language
    params.set_language(Some(&config.language));
    params.set_print_progress(config.verbose);
    params.set_print_realtime(false);
    params.set_print_timestamps(false);

    // Create a mutable state
    let mut state = ctx.create_state()
        .map_err(|e| ListenError::Transcription(format!("Failed to create state: {:?}", e)))?;

    // Run transcription
    state
        .full(params, samples)
        .map_err(|e| ListenError::Transcription(format!("Transcription failed: {:?}", e)))?;

    // Collect all text from segments using iterator
    let mut transcription = String::new();

    for segment in state.as_iter() {
        transcription.push_str(&format!("{}", segment));
    }

    Ok(transcription.trim().to_string())
}

fn load_audio_file(file_path: &str) -> Result<Vec<f32>> {
    // Try to read as WAV first
    if let Ok(mut reader) = hound::WavReader::open(file_path) {
        let spec = reader.spec();

        if spec.sample_rate != 16000 {
            return Err(ListenError::Audio(format!(
                "Audio must be 16kHz, got {}Hz. Use ffmpeg to convert:\n  \
                 ffmpeg -i {} -ar 16000 -ac 1 output.wav",
                spec.sample_rate, file_path
            )));
        }

        let samples: Vec<f32> = reader
            .samples::<i16>()
            .map(|s| s.unwrap() as f32 / 32768.0)
            .collect();

        return Ok(samples);
    }

    // For non-WAV files, user needs to convert first
    Err(ListenError::Audio(format!(
        "File format not supported directly. Convert to WAV first:\n  \
         ffmpeg -i {} -ar 16000 -ac 1 -f wav output.wav",
        file_path
    )))
}

fn get_model_path(model_name: &str) -> Result<String> {
    // Check for model in common locations
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());

    let candidates = vec![
        format!("{}/.cache/whisper/ggml-{}.bin", home, model_name),
        format!("/usr/share/whisper/ggml-{}.bin", model_name),
        format!("./models/ggml-{}.bin", model_name),
    ];

    for path in candidates {
        if Path::new(&path).exists() {
            return Ok(path);
        }
    }

    Err(ListenError::Config(format!(
        "Whisper model '{}' not found. Download it first:\n  \
         wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-{}.bin \\\n  \
         -P ~/.cache/whisper/",
        model_name, model_name
    )))
}

fn output_result(text: &str, config: &Config) -> Result<()> {
    if config.json {
        let output = serde_json::json!({
            "transcription": text,
            "language": config.language,
            "model": config.model,
        });
        println!("{}", serde_json::to_string_pretty(&output).unwrap());
    } else {
        println!("{}", text);
    }

    // Write to file if specified
    if let Some(output_file) = &config.output_file {
        std::fs::write(output_file, text)?;

        if !config.quiet {
            eprintln!("Saved to: {}", output_file);
        }
    }

    Ok(())
}
