import Foundation
import Vision
import AppKit

struct Tok {
    let text: String
    let x: CGFloat
    let y: CGFloat
    let w: CGFloat
    let h: CGFloat
    var midX: CGFloat { x + w / 2 }
    var midY: CGFloat { y + h / 2 }
}

let args = CommandLine.arguments
guard args.count >= 2 else {
    fputs("usage: table_ocr <image>...\n", stderr)
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
    try? handler.perform([request])
    var toks: [Tok] = []
    for o in request.results ?? [] {
        guard let s = o.topCandidates(1).first?.string else { continue }
        let b = o.boundingBox
        toks.append(Tok(text: s, x: b.minX, y: b.minY, w: b.width, h: b.height))
    }
    toks.sort { a, b in
        if abs(a.midY - b.midY) > 0.012 { return a.midY > b.midY }
        return a.midX < b.midX
    }
    print("===== \(url.lastPathComponent) =====")
    var rows: [[Tok]] = []
    for t in toks {
        if let last = rows.last, abs(last[0].midY - t.midY) < 0.012 {
            rows[rows.count - 1].append(t)
        } else {
            rows.append([t])
        }
    }
    for (i, row) in rows.enumerated() {
        let sorted = row.sorted { $0.midX < $1.midX }
        let cells = sorted.map { String(format: "%@ [x=%.3f]", $0.text, $0.midX) }
        print(String(format: "R%02d y=%.3f  %@", i, sorted[0].midY, cells.joined(separator: "  ")))
    }
    print()
}
