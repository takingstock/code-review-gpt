// swift-tools-version:5.3
import PackageDescription

let package = Package(
    name: "TreeSitterNodejsTs",
    products: [
        .library(name: "TreeSitterNodejsTs", targets: ["TreeSitterNodejsTs"]),
    ],
    dependencies: [
        .package(url: "https://github.com/ChimeHQ/SwiftTreeSitter", from: "0.8.0"),
    ],
    targets: [
        .target(
            name: "TreeSitterNodejsTs",
            dependencies: [],
            path: ".",
            exclude: [
                "Cargo.toml",
                "Makefile",
                "binding.gyp",
                "bindings/c",
                "bindings/go",
                "bindings/node",
                "bindings/python",
                "bindings/rust",
                "prebuilds",
                "grammar.js",
                "package.json",
                "package-lock.json",
                "pyproject.toml",
                "setup.py",
                "test",
                "examples",
                ".editorconfig",
                ".github",
                ".gitignore",
                ".gitattributes",
                ".gitmodules",
            ],
            sources: [
                "src/parser.c",
                // NOTE: if your language has an external scanner, add it here.
            ],
            resources: [
                .copy("queries")
            ],
            publicHeadersPath: "bindings/swift",
            cSettings: [.headerSearchPath("src")]
        ),
        .testTarget(
            name: "TreeSitterNodejsTsTests",
            dependencies: [
                "SwiftTreeSitter",
                "TreeSitterNodejsTs",
            ],
            path: "bindings/swift/TreeSitterNodejsTsTests"
        )
    ],
    cLanguageStandard: .c11
)
