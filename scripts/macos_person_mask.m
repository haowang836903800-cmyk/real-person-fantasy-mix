#import <Foundation/Foundation.h>
#import <Vision/Vision.h>
#import <CoreImage/CoreImage.h>
#import <CoreGraphics/CoreGraphics.h>
#import <CoreVideo/CoreVideo.h>
#import <ImageIO/ImageIO.h>

static void Stop(NSString *message) {
    fprintf(stderr, "error: %s\n", message.UTF8String);
    exit(1);
}

int main(int argc, const char *argv[]) {
    @autoreleasepool {
        if (argc != 3) {
            Stop(@"usage: macos_person_mask INPUT_IMAGE OUTPUT_MASK.png");
        }

        NSString *inputPath = [NSString stringWithUTF8String:argv[1]];
        NSString *outputPath = [NSString stringWithUTF8String:argv[2]];
        if (![[outputPath.pathExtension lowercaseString] isEqualToString:@"png"]) {
            Stop(@"output mask must be a PNG");
        }

        NSURL *inputURL = [NSURL fileURLWithPath:inputPath];
        NSURL *outputURL = [NSURL fileURLWithPath:outputPath];
        CGImageSourceRef source = CGImageSourceCreateWithURL((__bridge CFURLRef)inputURL, NULL);
        if (source == NULL) {
            Stop(@"cannot decode input image");
        }
        CGImageRef inputImage = CGImageSourceCreateImageAtIndex(source, 0, NULL);
        if (inputImage == NULL) {
            CFRelease(source);
            Stop(@"cannot decode input image");
        }
        NSDictionary *properties = CFBridgingRelease(CGImageSourceCopyPropertiesAtIndex(source, 0, NULL));
        NSNumber *orientationNumber = properties[(NSString *)kCGImagePropertyOrientation] ?: @1;
        CGImagePropertyOrientation orientation = (CGImagePropertyOrientation)orientationNumber.unsignedIntValue;
        BOOL swapsDimensions = orientation >= kCGImagePropertyOrientationLeftMirrored;
        size_t targetWidth = swapsDimensions ? CGImageGetHeight(inputImage) : CGImageGetWidth(inputImage);
        size_t targetHeight = swapsDimensions ? CGImageGetWidth(inputImage) : CGImageGetHeight(inputImage);

        VNGeneratePersonSegmentationRequest *request = [[VNGeneratePersonSegmentationRequest alloc] init];
        request.qualityLevel = VNGeneratePersonSegmentationRequestQualityLevelAccurate;
        request.outputPixelFormat = kCVPixelFormatType_OneComponent8;
        request.usesCPUOnly = YES;

        VNImageRequestHandler *handler = [[VNImageRequestHandler alloc] initWithCGImage:inputImage orientation:orientation options:@{}];
        NSError *requestError = nil;
        if (![handler performRequests:@[request] error:&requestError]) {
            Stop([NSString stringWithFormat:@"Vision person segmentation failed: %@", requestError.localizedDescription]);
        }

        VNPixelBufferObservation *observation = request.results.firstObject;
        if (observation == nil) {
            Stop(@"no person was detected");
        }

        CIImage *maskImage = [CIImage imageWithCVPixelBuffer:observation.pixelBuffer];
        CGFloat scaleX = (CGFloat)targetWidth / CGRectGetWidth(maskImage.extent);
        CGFloat scaleY = (CGFloat)targetHeight / CGRectGetHeight(maskImage.extent);
        CGAffineTransform transform = CGAffineTransformMakeScale(scaleX, scaleY);
        CIImage *scaledMask = [maskImage imageByApplyingTransform:transform];
        scaledMask = [scaledMask imageByCroppingToRect:CGRectMake(0, 0, targetWidth, targetHeight)];

        CIContext *context = [CIContext contextWithOptions:@{ kCIContextUseSoftwareRenderer: @NO }];
        CGColorSpaceRef gray = CGColorSpaceCreateDeviceGray();
        NSError *writeError = nil;
        BOOL wrote = [context writePNGRepresentationOfImage:scaledMask
                                                      toURL:outputURL
                                                     format:kCIFormatL8
                                                 colorSpace:gray
                                                    options:@{}
                                                      error:&writeError];
        CGColorSpaceRelease(gray);
        if (!wrote) {
            Stop([NSString stringWithFormat:@"cannot write mask PNG: %@", writeError.localizedDescription]);
        }

        CGImageRelease(inputImage);
        CFRelease(source);
        printf("person mask: %zux%zu -> %s\n", targetWidth, targetHeight, outputPath.UTF8String);
    }
    return 0;
}
