use thiserror::Error;

#[derive(Error, Debug)]
pub enum ListenError {
    #[error("Audio error: {0}")]
    Audio(String),

    #[error("Transcription error: {0}")]
    Transcription(String),

    #[error("File error: {0}")]
    File(#[from] std::io::Error),

    #[error("Configuration error: {0}")]
    Config(String),

    #[error("Signal error: {0}")]
    Signal(String),
}

pub type Result<T> = std::result::Result<T, ListenError>;
