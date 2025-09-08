"""Audio processing utilities for the Teams Interview Bot."""

import logging
import wave
import numpy as np
from typing import Optional, Tuple
import io

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Utility class for audio processing operations."""
    
    @staticmethod
    def convert_audio_format(
        audio_data: bytes,
        source_format: str = "wav",
        target_format: str = "pcm",
        sample_rate: int = 16000,
        channels: int = 1
    ) -> Optional[bytes]:
        """
        Convert audio data between different formats.
        
        Args:
            audio_data: Raw audio data
            source_format: Source audio format
            target_format: Target audio format
            sample_rate: Audio sample rate
            channels: Number of audio channels
            
        Returns:
            Converted audio data or None if conversion fails
        """
        try:
            if source_format == "wav" and target_format == "pcm":
                # Convert WAV to PCM
                with io.BytesIO(audio_data) as wav_buffer:
                    with wave.open(wav_buffer, 'rb') as wav_file:
                        frames = wav_file.readframes(wav_file.getnframes())
                        return frames
            
            elif source_format == "pcm" and target_format == "wav":
                # Convert PCM to WAV
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(channels)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data)
                
                return wav_buffer.getvalue()
            
            else:
                logger.warning(f"Unsupported audio conversion: {source_format} -> {target_format}")
                return audio_data
                
        except Exception as e:
            logger.error(f"Error converting audio format: {str(e)}")
            return None
    
    @staticmethod
    def apply_noise_reduction(audio_data: bytes, sample_rate: int = 16000) -> bytes:
        """
        Apply basic noise reduction to audio data.
        
        Args:
            audio_data: Raw audio data
            sample_rate: Audio sample rate
            
        Returns:
            Processed audio data with reduced noise
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Apply simple noise gate (remove very quiet sounds)
            threshold = np.max(np.abs(audio_array)) * 0.1
            audio_array[np.abs(audio_array) < threshold] = 0
            
            # Apply simple low-pass filter to reduce high-frequency noise
            # This is a basic implementation - in production, use proper DSP libraries
            if len(audio_array) > 1:
                filtered = np.convolve(audio_array, [0.25, 0.5, 0.25], mode='same')
                audio_array = filtered.astype(np.int16)
            
            return audio_array.tobytes()
            
        except Exception as e:
            logger.error(f"Error applying noise reduction: {str(e)}")
            return audio_data
    
    @staticmethod
    def normalize_audio_volume(audio_data: bytes, target_level: float = 0.8) -> bytes:
        """
        Normalize audio volume to a target level.
        
        Args:
            audio_data: Raw audio data
            target_level: Target volume level (0.0 to 1.0)
            
        Returns:
            Volume-normalized audio data
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            if len(audio_array) == 0:
                return audio_data
            
            # Calculate current peak level
            current_peak = np.max(np.abs(audio_array))
            
            if current_peak == 0:
                return audio_data
            
            # Calculate normalization factor
            max_int16 = 32767
            target_peak = max_int16 * target_level
            normalization_factor = target_peak / current_peak
            
            # Apply normalization
            normalized_array = audio_array * normalization_factor
            normalized_array = np.clip(normalized_array, -max_int16, max_int16)
            
            return normalized_array.astype(np.int16).tobytes()
            
        except Exception as e:
            logger.error(f"Error normalizing audio volume: {str(e)}")
            return audio_data
    
    @staticmethod
    def detect_speech_activity(
        audio_data: bytes,
        sample_rate: int = 16000,
        frame_duration_ms: int = 30
    ) -> bool:
        """
        Detect if audio data contains speech activity.
        
        Args:
            audio_data: Raw audio data
            sample_rate: Audio sample rate
            frame_duration_ms: Frame duration in milliseconds
            
        Returns:
            True if speech activity detected, False otherwise
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            if len(audio_array) == 0:
                return False
            
            # Calculate frame size
            frame_size = int(sample_rate * frame_duration_ms / 1000)
            
            # Calculate energy levels
            energy_levels = []
            for i in range(0, len(audio_array) - frame_size, frame_size):
                frame = audio_array[i:i + frame_size]
                energy = np.sum(frame.astype(np.float64) ** 2) / len(frame)
                energy_levels.append(energy)
            
            if not energy_levels:
                return False
            
            # Simple voice activity detection based on energy threshold
            avg_energy = np.mean(energy_levels)
            max_energy = np.max(energy_levels)
            
            # Threshold based on dynamic range
            threshold = avg_energy * 2.0
            
            # Check if any frame exceeds threshold
            return max_energy > threshold
            
        except Exception as e:
            logger.error(f"Error detecting speech activity: {str(e)}")
            return False
    
    @staticmethod
    def split_audio_by_silence(
        audio_data: bytes,
        sample_rate: int = 16000,
        silence_threshold: float = 0.01,
        min_silence_duration_ms: int = 500
    ) -> list:
        """
        Split audio data by silence periods.
        
        Args:
            audio_data: Raw audio data
            sample_rate: Audio sample rate
            silence_threshold: Silence detection threshold
            min_silence_duration_ms: Minimum silence duration to split on
            
        Returns:
            List of audio segments
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            if len(audio_array) == 0:
                return []
            
            # Normalize audio for threshold comparison
            normalized_audio = audio_array.astype(np.float32) / 32767.0
            
            # Calculate minimum silence samples
            min_silence_samples = int(sample_rate * min_silence_duration_ms / 1000)
            
            # Find silence regions
            is_silence = np.abs(normalized_audio) < silence_threshold
            
            # Find silence boundaries
            silence_changes = np.diff(is_silence.astype(int))
            silence_starts = np.where(silence_changes == 1)[0] + 1
            silence_ends = np.where(silence_changes == -1)[0] + 1
            
            # Handle edge cases
            if is_silence[0]:
                silence_starts = np.concatenate([[0], silence_starts])
            if is_silence[-1]:
                silence_ends = np.concatenate([silence_ends, [len(audio_array)]])
            
            # Filter by minimum duration
            valid_silences = []
            for start, end in zip(silence_starts, silence_ends):
                if end - start >= min_silence_samples:
                    valid_silences.append((start, end))
            
            # Split audio at silence boundaries
            segments = []
            last_end = 0
            
            for silence_start, silence_end in valid_silences:
                if silence_start > last_end:
                    segment = audio_array[last_end:silence_start]
                    if len(segment) > 0:
                        segments.append(segment.tobytes())
                last_end = silence_end
            
            # Add final segment
            if last_end < len(audio_array):
                segment = audio_array[last_end:]
                if len(segment) > 0:
                    segments.append(segment.tobytes())
            
            return segments
            
        except Exception as e:
            logger.error(f"Error splitting audio by silence: {str(e)}")
            return [audio_data]
    
    @staticmethod
    def calculate_audio_metrics(audio_data: bytes, sample_rate: int = 16000) -> dict:
        """
        Calculate various audio quality metrics.
        
        Args:
            audio_data: Raw audio data
            sample_rate: Audio sample rate
            
        Returns:
            Dictionary containing audio metrics
        """
        try:
            # Convert bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            if len(audio_array) == 0:
                return {}
            
            # Calculate basic metrics
            duration_seconds = len(audio_array) / sample_rate
            rms_level = np.sqrt(np.mean(audio_array.astype(np.float64) ** 2))
            peak_level = np.max(np.abs(audio_array))
            
            # Calculate signal-to-noise ratio (simplified)
            # This is a basic estimation - proper SNR calculation requires noise reference
            sorted_samples = np.sort(np.abs(audio_array))
            noise_floor = np.mean(sorted_samples[:len(sorted_samples)//10])  # Bottom 10%
            signal_level = np.mean(sorted_samples[-len(sorted_samples)//10:])  # Top 10%
            
            snr_db = 20 * np.log10(signal_level / max(noise_floor, 1)) if noise_floor > 0 else 0
            
            # Calculate zero crossing rate (indicator of speech vs noise)
            zero_crossings = np.sum(np.diff(np.sign(audio_array)) != 0)
            zcr = zero_crossings / len(audio_array)
            
            return {
                "duration_seconds": duration_seconds,
                "sample_rate": sample_rate,
                "rms_level": float(rms_level),
                "peak_level": float(peak_level),
                "estimated_snr_db": float(snr_db),
                "zero_crossing_rate": float(zcr),
                "dynamic_range_db": 20 * np.log10(peak_level / max(rms_level, 1)) if rms_level > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating audio metrics: {str(e)}")
            return {}