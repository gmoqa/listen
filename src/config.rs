use crate::cli::Args;
use crate::error::{ListenError, Result};
use serde::{Deserialize, Serialize};

/// Audio configuration constants
pub const SAMPLE_RATE: u32 = 16000;
pub const CHANNELS: u16 = 1;
pub const VAD_DEFAULT_DURATION: f32 = 2.0;
pub const VAD_THRESHOLD: f32 = 0.02;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub language: String,
    pub model: String,
    pub signal_mode: bool,
    pub vad_enabled: bool,
    pub vad_duration: f32,
    pub vad_threshold: f32,
    pub codevoice: bool,
    pub fast_mode: bool,
    pub verbose: bool,
    pub quiet: bool,
    pub json: bool,
    pub output_file: Option<String>,
    pub status_file: Option<String>,
    pub sample_rate: u32,
    pub channels: u16,
}

impl Config {
    pub fn from_args(args: &Args) -> Result<Self> {
        let vad_enabled = args.vad.is_some();
        let vad_duration = args.vad.unwrap_or(VAD_DEFAULT_DURATION);

        if vad_enabled && vad_duration <= 0.0 {
            return Err(ListenError::Config(
                "VAD duration must be positive".to_string(),
            ));
        }

        Ok(Config {
            language: args.language.clone(),
            model: args.model.clone(),
            signal_mode: args.signal_mode,
            vad_enabled,
            vad_duration,
            vad_threshold: VAD_THRESHOLD,
            codevoice: args.codevoice,
            fast_mode: args.fast_mode,
            verbose: args.verbose,
            quiet: args.quiet,
            json: args.json,
            output_file: args.output.clone(),
            status_file: args.status_file.clone(),
            sample_rate: SAMPLE_RATE,
            channels: CHANNELS,
        })
    }
}
