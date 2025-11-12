use clap::Parser;

#[derive(Parser, Debug)]
#[command(name = "listen")]
#[command(author = "Guillermo Quinteros <gu.quinteros@gmail.com>")]
#[command(version)]
#[command(about = "Minimal audio transcription tool - 100% on-premise", long_about = None)]
pub struct Args {
    /// Transcribe audio from file (mp3, wav, m4a, etc.)
    #[arg(short, long, value_name = "FILE")]
    pub file: Option<String>,

    /// Language code (e.g., es, en, fr)
    #[arg(short, long, default_value = "es")]
    pub language: String,

    /// Whisper model (tiny, base, small, medium, large)
    #[arg(short, long, default_value = "base")]
    pub model: String,

    /// Use SIGUSR1 signal to stop recording
    #[arg(long)]
    pub signal_mode: bool,

    /// Auto-stop after N seconds of silence
    #[arg(long, value_name = "SECONDS")]
    pub vad: Option<f32>,

    /// Full-width visual mode for code voice input
    #[arg(long)]
    pub codevoice: bool,

    /// Use faster-whisper for 3-4x speed
    #[arg(long)]
    pub fast_mode: bool,

    /// Verbose output
    #[arg(short, long)]
    pub verbose: bool,

    /// Suppress UI, output only transcription
    #[arg(short, long)]
    pub quiet: bool,

    /// Output in JSON format
    #[arg(short, long)]
    pub json: bool,

    /// Write transcription to file
    #[arg(short, long, value_name = "FILE")]
    pub output: Option<String>,

    /// Write real-time status to JSON file
    #[arg(long, value_name = "FILE")]
    pub status_file: Option<String>,
}
