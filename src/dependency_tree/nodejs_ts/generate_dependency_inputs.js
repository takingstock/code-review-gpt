const fs = require('fs');
const path = require('path');

// Helper function to read the diff from a file
function readDiffFromFile(filePath) {
    return fs.readFileSync(filePath, 'utf8');
}

// Helper function to extract changed files and methods
function parseGitDiff(diffOutput) {
    const lines = diffOutput.split('\n');
    const changes = { py: [], nodejs: [] };

    let currentFile = null;
    let currentLanguage = null;

    lines.forEach(line => {
        if (line.startsWith('diff --git')) {
            // Extract file path and determine language
            const filePath = line.split(' ')[2].slice(2); // strip 'a/'
            currentFile = filePath;
            const ext = path.extname(filePath);
            if ( ext === '.py' ){
		    currentLanguage = 'py';
	    }
	    else if ( ext === '.js' ){
		    currentLanguage = 'nodejs';
	    }
        }

	if ( currentLanguage === null ){
		return;
	}

        if (line.startsWith('@@')) {
            const methodName = extractMethodName(currentFile, line, currentLanguage);

	    if (!changes[currentLanguage].some(entry => entry.changed_file === currentFile)) {	
               if (methodName) {
                 changes[currentLanguage].push({
                    changed_file: currentFile,
                    method_nm: methodName,
                  });
               } else {
                 changes[currentLanguage].push({
                    changed_file: currentFile,
                    method_nm: 'global scope',
                 });
               }
	    }
        }
    });

    return changes;
}

// Extract method name based on language
function extractMethodName(filePath, diffLine, language) {
    // Placeholder for actual method extraction logic
    // In a real scenario, this function would read the file and use regex/parsers to identify the method name
    if (language === 'py') {
        const match = diffLine.match(/def\s+(\w+)\(/);
        return match ? match[1] : null;
    } else if (language === 'nodejs') {
        const match = diffLine.match( /(?:const|let|var)\s+(\w+)\s*=\s*\(?.*?\)?\s*=>/ );
        if ( match ){
	  return match[1];
	}
	// we could have added this to the above BUT for some reason its flunking    
        const match_fn_ = diffLine.match( /(?:function\s+(\w+)|(const|let|var)\s+(\w+)\s*=\s*\(?.*?\)?\s*=>)/ );
        return match_fn_ ? match_fn_[1] : null;
    }
    return null;
}

function generateInput( git_diff_op=process.env.GIT_DIFF_FILE, dependency_input_file_=process.env.CHANGES_JSON ){
    try {	
      // Read the diff from the file
      const diffContent = readDiffFromFile( git_diff_op );

      // Parse the diff and output the changes
      const changes = parseGitDiff( diffContent );
      fs.writeFileSync( dependency_input_file_, JSON.stringify( changes, null, 2 ), 'utf-8' );

    } catch (err) {	
      
      fs.writeFileSync( dependency_input_file_, JSON.stringify( {}, null, 2 ), 'utf-8' );

    }
}

generateInput();
