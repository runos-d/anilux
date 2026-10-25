import SwiftUI
import WebKit

@main
struct AniLuxApp: App {
    var body: some Scene { WindowGroup { Website().ignoresSafeArea(.container, edges: .bottom) } }
}

struct Website: UIViewRepresentable {
    func makeCoordinator() -> Navigation { Navigation() }
    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        configuration.allowsPictureInPictureMediaPlayback = true
        let view = WKWebView(frame: .zero, configuration: configuration)
        view.navigationDelegate = context.coordinator
        view.allowsBackForwardNavigationGestures = true
        let data = try! Data(contentsOf: Bundle.main.url(forResource: "Site", withExtension: "json")!)
        let config = try! JSONDecoder().decode(Site.self, from: data)
        context.coordinator.site = URL(string: config.siteUrl)!
        view.load(URLRequest(url: context.coordinator.site))
        return view
    }
    func updateUIView(_ view: WKWebView, context: Context) {}
    struct Site: Decodable { var siteUrl: String }
    class Navigation: NSObject, WKNavigationDelegate {
        var site: URL!
        func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            guard let url = action.request.url else { decisionHandler(.cancel); return }
            if action.targetFrame?.isMainFrame == false { decisionHandler(.allow); return }
            if url.scheme == site.scheme && url.host == site.host && url.port == site.port {
                decisionHandler(.allow)
            } else {
                decisionHandler(.cancel)
                if action.navigationType == .linkActivated && ["https", "mailto", "tel"].contains(url.scheme ?? "") { UIApplication.shared.open(url) }
            }
        }
    }
}
