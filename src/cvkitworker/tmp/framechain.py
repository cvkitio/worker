'''
Goal is to have a basic base class for a video frame and an iterator that holds a series of frames and
a chain of processing classes that can be applied to each frame in order with a chain of inputs/outputs
The processing subclasses we would have are
Preocessor - with subclasses like scale, resize, convert color space, blur etc, outputs a frame
Detector - takes a Frame and performs computer vision functions like object detection, fave liveness, face match etc 
and outputs a frame + metadata: a Detection which would include things like the detection name and region polygon
or None if nothing detected just outputs the input frame
Markuper - takes data from the Detector and marks up a Frame e.g. drawing boxes for the polygon, outputs a Frame
Outputer - Takes a frame and writes it to an output such as a file, stream, display etc
This would generally work like this:
PreProcessor -> Detector -> Markup -> Output

So the FrameProcessor would have appended to it Frames
The FrameProcessor would also be initialised with a ProcessorChain e.g.
Scale -> Grayscale -> FaceDetect -> FaceMatch -> MarkupFaceMatch -> OutputFile
The FrameProcssor should have an option so that when a frame is appended it triggers a process method call or that can be called independently
This also needs to be setup so that is can run in a multi processing setup where the producer appends the frames
but the consumers do the frame processing. Currently this is done using a shared memory object
'''


from dataclasses import dataclass

@dataclass
class Frame():
    width: int
    height: int
    color_space: str
    bit_depth: int
    frame_data: bytes = None  # Placeholder for frame data, could be an image or video frame
    
class FrameProcess(Frame):
    def __init__(self, width: int, height: int, color_space: str, bit_depth: int):
        super().__init__(width, height, color_space, bit_depth)
        self.processed_data = None  # Placeholder for processed frame data

    def process(self, frame: Frame) -> Frame:
        '''
        Generic class for taking a frame and processing it and returning a frame
        '''
        # Placeholder for actual processing logic
        
        return frame

class Detector(FrameProcess):
    def __init__(self):
        super().__init__()
        
    def process(self, frame: Frame) -> Frame:
        '''
        Implement detection logic here
        '''
        pass
    
@dataclass
class Detection(Frame):
    x: int
    y: int
    width: int
    height: int
    # TODO have a polygon for the detection area
    confidence: float
    label: str = None
        
        
class FaceDetector(Detector):
    def __init__(self):
        super().__init__()
        self.name = "FaceDetector"
        self.model = None  # Placeholder for the model, e.g., a pre-trained face detection model
        self.confidence_threshold = 0.5  # Default confidence threshold for detections
    
    def detect(self, frame: Frame):
        '''
        Implement face detection logic here
        '''
        super.detect(frame)
        
        return frame  
    
def PreProcessor(FrameProcess):
    '''
    A class that provides functions for preprocessing frames
    '''
    def __init__(self):
        super().__init__()
    
    def process(self, frame: Frame) -> Frame:
        '''
        Implement preprocessing logic here
        '''
        return frame  # Placeholder, should return a preprocessed frame

def PreProcessorGrayscale(PreProcessor):
    '''
    A class that provides functions for preprocessing frames to grayscale
    '''
    def __init__(self):
        super().__init__()
    
    def preprocess(self, frame: Frame) -> Frame:
        '''
        Convert the frame to grayscale
        '''
        # Placeholder for actual grayscale conversion logic
        frame.color_space = 'grayscale'
        return frame  # Should return a grayscale frame

class FrameProcessor():
    '''
    A class that provides functions for a list of frames to process
    '''
    def __init__(self):
        self.frames = []
        self.index = 0
        pass
    
    def __next__():
        pass
    
    def append_frame(self, frame: Frame):
        '''
        Append a frame to the list of frames
        '''
        self.frames.append(frame)
    
    
