#!/usr/bin/env python3
"""
Automated test for face detection using Kaggle-based test video.

This test verifies that the face detection system correctly identifies faces
and no-face frames in a test video created from Kaggle human faces dataset.
"""

import cv2
import json
import time
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any

# Import our detection modules
from detect.detectors.face_detect import FaceDetector


class KaggleFaceDetectionTester:
    """Test face detection against Kaggle-based ground truth."""
    
    def __init__(self, video_path: str, metadata_path: str):
        self.video_path = Path(video_path)
        self.metadata_path = Path(metadata_path)
        self.metadata = None
        self.load_metadata()
        
    def load_metadata(self):
        """Load test video metadata with ground truth."""
        with open(self.metadata_path, 'r') as f:
            self.metadata = json.load(f)
        logger.info(f"Loaded metadata for {len(self.metadata['frames'])} frames")
        
    def get_expected_result_for_frame(self, frame_number: int) -> Dict[str, Any]:
        """Get expected detection result for the given frame."""
        if frame_number < len(self.metadata['frames']):
            return self.metadata['frames'][frame_number]
        return None
    
    def test_single_frame(self, frame_number: int, frame: any) -> Dict[str, Any]:
        """Test face detection on a single frame."""
        expected_result = self.get_expected_result_for_frame(frame_number)
        
        if not expected_result:
            return {
                "frame_number": frame_number,
                "error": "No metadata for this frame",
                "success": False
            }
        
        # Initialize face detector - try both dlib and dlib_cnn
        detectors_to_try = ["dlib", "dlib_cnn"]
        best_result = None
        
        for detector_name in detectors_to_try:
            try:
                face_detector = FaceDetector(detector_name)
                
                # Detect faces in the frame
                start_time = time.time()
                detected_faces = face_detector.detect(frame)
                detection_time = (time.time() - start_time) * 1000
                
                # Analyze results
                result = {
                    "frame_number": frame_number,
                    "detector_used": detector_name,
                    "expected_has_face": expected_result['has_face'],
                    "detected_face_count": len(detected_faces) if detected_faces else 0,
                    "detection_time_ms": detection_time,
                    "detected_faces": detected_faces,
                    "expected_info": expected_result,
                    "success": False,
                    "message": ""
                }
                
                # Check if detection matches expectation
                if expected_result['has_face']:
                    # Should detect at least one face
                    if result["detected_face_count"] > 0:
                        result["success"] = True
                        result["message"] = f"✓ Correctly detected {result['detected_face_count']} face(s) with {detector_name}"
                        return result  # Return immediately on success
                    else:
                        result["success"] = False
                        result["message"] = f"✗ Failed to detect expected face with {detector_name}"
                else:
                    # Should not detect any faces
                    if result["detected_face_count"] == 0:
                        result["success"] = True
                        result["message"] = f"✓ Correctly detected no faces with {detector_name}"
                        return result  # Return immediately on success
                    else:
                        result["success"] = False
                        result["message"] = f"✗ False positive: detected {result['detected_face_count']} face(s) when none expected with {detector_name}"
                
                # Store best result (first non-errored attempt)
                if best_result is None:
                    best_result = result
                    
            except Exception as e:
                logger.warning(f"Detector {detector_name} failed: {e}")
                continue
        
        return best_result if best_result else {
            "frame_number": frame_number,
            "error": "All detectors failed",
            "success": False
        }
    
    def test_all_frames(self) -> List[Dict[str, Any]]:
        """Test face detection on all frames from the video."""
        logger.info(f"Testing face detection on video: {self.video_path}")
        
        # Open video
        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            logger.error(f"Could not open video: {self.video_path}")
            return []
        
        results = []
        frame_number = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            logger.info(f"Testing frame {frame_number}")
            
            # Test this frame
            result = self.test_single_frame(frame_number, frame)
            results.append(result)
            
            logger.info(f"Frame {frame_number}: {result.get('message', 'No message')}")
            frame_number += 1
        
        cap.release()
        return results
    
    def run_full_test(self) -> Dict[str, Any]:
        """Run complete face detection test."""
        logger.info("Starting Kaggle face detection test")
        
        start_time = time.time()
        frame_results = self.test_all_frames()
        total_time = time.time() - start_time
        
        # Analyze overall results
        total_tests = len(frame_results)
        successful_tests = sum(1 for r in frame_results if r.get('success', False))
        
        # Separate results by expected face/no-face
        face_frames = [r for r in frame_results if r.get('expected_has_face', False)]
        no_face_frames = [r for r in frame_results if not r.get('expected_has_face', True)]
        
        face_successes = sum(1 for r in face_frames if r.get('success', False))
        no_face_successes = sum(1 for r in no_face_frames if r.get('success', False))
        
        summary = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": successful_tests / total_tests if total_tests > 0 else 0,
            
            "face_frame_tests": len(face_frames),
            "face_frame_successes": face_successes,
            "face_detection_rate": face_successes / len(face_frames) if face_frames else 0,
            
            "no_face_frame_tests": len(no_face_frames),
            "no_face_frame_successes": no_face_successes,
            "no_face_accuracy": no_face_successes / len(no_face_frames) if no_face_frames else 0,
            
            "total_time_seconds": total_time,
            "frame_results": frame_results
        }
        
        # Log summary
        logger.info(f"Test completed: {successful_tests}/{total_tests} tests passed")
        logger.info(f"Overall success rate: {summary['success_rate']:.2%}")
        logger.info(f"Face detection rate: {summary['face_detection_rate']:.2%} ({face_successes}/{len(face_frames)})")
        logger.info(f"No-face accuracy: {summary['no_face_accuracy']:.2%} ({no_face_successes}/{len(no_face_frames)})")
        logger.info(f"Total time: {total_time:.2f} seconds")
        
        return summary


def main():
    """Main test function."""
    video_path = "test_data_kaggle/test_faces_kaggle.mp4"
    metadata_path = "test_data_kaggle/test_metadata.json"
    
    # Check if test files exist
    if not Path(video_path).exists():
        logger.error(f"Test video not found: {video_path}")
        logger.info("Run 'python create_kaggle_test_dataset.py' first to create test data")
        return False
    
    if not Path(metadata_path).exists():
        logger.error(f"Test metadata not found: {metadata_path}")
        return False
    
    # Run test
    tester = KaggleFaceDetectionTester(video_path, metadata_path)
    results = tester.run_full_test()
    
    # Save results
    results_path = Path("test_data_kaggle/face_detection_test_results.json")
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Test results saved to: {results_path}")
    
    # Print detailed summary
    print(f"\n=== KAGGLE FACE DETECTION TEST RESULTS ===")
    print(f"Total tests: {results['total_tests']}")
    print(f"Passed: {results['successful_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Overall success rate: {results['success_rate']:.2%}")
    print(f"")
    print(f"Face detection performance:")
    print(f"  Face frames tested: {results['face_frame_tests']}")
    print(f"  Faces detected: {results['face_frame_successes']}")
    print(f"  Face detection rate: {results['face_detection_rate']:.2%}")
    print(f"")
    print(f"No-face detection performance:")
    print(f"  No-face frames tested: {results['no_face_frame_tests']}")
    print(f"  Correctly identified as no-face: {results['no_face_frame_successes']}")
    print(f"  No-face accuracy: {results['no_face_accuracy']:.2%}")
    print(f"")
    print(f"Total time: {results['total_time_seconds']:.2f}s")
    
    # Show detailed results
    print(f"\nDetailed frame results:")
    for result in results['frame_results']:
        status = "✓" if result.get('success', False) else "✗"
        face_expected = "FACE" if result.get('expected_has_face', False) else "NO FACE"
        detected = result.get('detected_face_count', 0)
        detector = result.get('detector_used', 'unknown')
        print(f"  Frame {result['frame_number']}: {status} Expected: {face_expected}, Detected: {detected} faces ({detector})")
    
    if results['failed_tests'] > 0:
        print(f"\nFailed tests:")
        for result in results['frame_results']:
            if not result.get('success', True):
                print(f"  Frame {result['frame_number']}: {result.get('message', 'Unknown error')}")
    
    # Return True if success rate is good (>= 70%)
    return results['success_rate'] >= 0.7


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)