import Foundation
import Vision
import AppKit

let args = CommandLine.arguments
guard args.count >= 2 else {
    fputs("usage: vision_ocr <image> [image...]\n", stderr)
    exit(1)
}

for path in args.dropFirst() {
    let url = URL(fileURLWithPath: path)
    guard let img = NSImage(contentsOf: url),
          let tiff = img.tiffRepresentation,
          let ci = CIImage(data: tiff) else {
        print("FAIL \(path)")
        continue
    }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.usesLanguageCorrection = false
    request.recognitionLanguages = ["en-US"]
    let handler = VNImageRequestHandler(ciImage: ci, options: [:])
    do {
        try handler.perform([request])
    } catch {
        print("ERR \(path) \(error)")
        continue
    }
    print("===== \(url.lastPathComponent) =====")
    let obs = (request.results ?? []).sorted { a, b in
        let ab = a.boundingBox
        let bb = b.boundingBox
        if abs(ab.midY - bb.midY) > 0.015 {
            return ab.midY > bb.midY
        }
        return ab.minX < bb.minX
    }
    var lineY: CGFloat = -1
    var line: [String] = []
    func flush() {
        if !line.isEmpty {
            print(line.joined(separator: " | "))
            line = []
        }
    }
    for o in obs {
        guard let s = o.topCandidates(1).first?.string else { continue }
        let y = o.boundingBox.midY
        if lineY < 0 || abs(y - lineY) < 0.015 {
            line.append(s)
            lineY = line.isEmpty ? y : (lineY + y) / 2
        } else {
            flush()
            line = [s]
            lineY = y
        }
    }
    flush()
    print()
}
