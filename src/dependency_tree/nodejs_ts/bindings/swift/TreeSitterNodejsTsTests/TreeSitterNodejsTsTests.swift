import XCTest
import SwiftTreeSitter
import TreeSitterNodejsTs

final class TreeSitterNodejsTsTests: XCTestCase {
    func testCanLoadGrammar() throws {
        let parser = Parser()
        let language = Language(language: tree_sitter_nodejs_ts())
        XCTAssertNoThrow(try parser.setLanguage(language),
                         "Error loading NodejsTs grammar")
    }
}
