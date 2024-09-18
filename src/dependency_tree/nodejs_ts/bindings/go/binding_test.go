package tree_sitter_nodejs_ts_test

import (
	"testing"

	tree_sitter "github.com/tree-sitter/go-tree-sitter"
	tree_sitter_nodejs_ts "github.com/tree-sitter/tree-sitter-nodejs_ts/bindings/go"
)

func TestCanLoadGrammar(t *testing.T) {
	language := tree_sitter.NewLanguage(tree_sitter_nodejs_ts.Language())
	if language == nil {
		t.Errorf("Error loading NodejsTs grammar")
	}
}
