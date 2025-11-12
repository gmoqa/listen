use crate::config::Config;
use crate::error::{ListenError, Result};
use crate::transcribe;
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::{Arc, Mutex};
use std::io::Write;

pub async fn record_and_transcribe(config: &Config) -> Result<()> {
    if !config.quiet {
        print_recording_start(config);
    }

    // Record audio from microphone
    let audio_data = record_audio(config)?;

    if !config.quiet {
        println!("\n\n● Processing...");
    }

    // Transcribe the recorded audio
    let transcription = transcribe::transcribe_buffer(&audio_data, config).await?;

    // Output results
    output_transcription(&transcription, config)?;

    Ok(())
}

fn print_recording_start(config: &Config) {
    println!("\x1b[2J\x1b[H"); // Clear screen and home cursor
    println!("● Recording... Press SPACE to stop");

    if config.signal_mode {
        println!("  (or send SIGUSR1: kill -SIGUSR1 {})", std::process::id());
    }

    if config.vad_enabled {
        println!("  (auto-stop after {:.1}s of silence)", config.vad_duration);
    }
}

fn record_audio(config: &Config) -> Result<Vec<f32>> {
    let host = cpal::default_host();

    let device = host
        .default_input_device()
        .ok_or_else(|| ListenError::Audio("No input device found".to_string()))?;

    if config.verbose {
        println!("[DEBUG] Using device: {}", device.name().unwrap_or_default());
    }

    let cpal_config = cpal::StreamConfig {
        channels: config.channels,
        sample_rate: cpal::SampleRate(config.sample_rate),
        buffer_size: cpal::BufferSize::Default,
    };

    let recorded_samples = Arc::new(Mutex::new(Vec::new()));
    let recorded_samples_clone = recorded_samples.clone();

    let err_fn = |err| eprintln!("Audio stream error: {}", err);

    let stream = device
        .build_input_stream(
            &cpal_config,
            move |data: &[f32], _: &cpal::InputCallbackInfo| {
                let mut samples = recorded_samples_clone.lock().unwrap();
                samples.extend_from_slice(data);
            },
            err_fn,
            None,
        )
        .map_err(|e| ListenError::Audio(format!("Failed to build stream: {}", e)))?;

    stream
        .play()
        .map_err(|e| ListenError::Audio(format!("Failed to start stream: {}", e)))?;

    // Wait for space key press
    wait_for_stop_signal(config)?;

    drop(stream);

    let samples = recorded_samples.lock().unwrap().clone();

    if config.verbose {
        println!("[DEBUG] Recorded {} samples", samples.len());
    }

    Ok(samples)
}

fn wait_for_stop_signal(config: &Config) -> Result<()> {
    use std::io::Read;

    if config.signal_mode {
        // TODO: Implement SIGUSR1 signal handling
        std::thread::sleep(std::time::Duration::from_secs(30));
    } else {
        // Wait for spacebar
        let mut stdin = std::io::stdin();
        let mut buffer = [0u8; 1];

        loop {
            if stdin.read_exact(&mut buffer).is_ok() {
                if buffer[0] == b' ' || buffer[0] == b'\n' {
                    break;
                }
            }
        }
    }

    Ok(())
}

fn output_transcription(text: &str, config: &Config) -> Result<()> {
    if config.json {
        let output = serde_json::json!({
            "transcription": text,
            "language": config.language,
            "model": config.model,
        });
        println!("{}", serde_json::to_string_pretty(&output).unwrap());
    } else if !config.quiet {
        println!("\n{}", text);
    } else {
        println!("{}", text);
    }

    // Write to file if specified
    if let Some(output_file) = &config.output_file {
        std::fs::write(output_file, text)
            .map_err(|e| ListenError::File(e))?;

        if !config.quiet {
            println!("\nSaved to: {}", output_file);
        }
    }

    Ok(())
}
