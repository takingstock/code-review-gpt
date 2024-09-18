const Parser = require('tree-sitter');
const JavaScript = require('tree-sitter-javascript');
const fs = require('fs');
const path = require('path');

const options = {
      bufferSize: 1024 * 1024, // Set the bufferSize to 1 MB (1024 KB)
};

// Initialize the parser
const parser = new Parser();
parser.setLanguage(JavaScript);

// Function to parse the JS file and extract assignments and method details
function parseFileDetails(filePath) {
  const code = fs.readFileSync(filePath, 'utf8');
  const tree = parser.parse( code, undefined, options );

  const results = {}; // Dictionary to store the results

  function getEnclosingMethodName(node) {
	  let methodNode = node;

	  // Traverse up the AST to find the enclosing function/method
	  while (
	    methodNode && 
	    methodNode.type !== 'function_declaration' &&
	    methodNode.type !== 'method_definition' &&
	    methodNode.type !== 'arrow_function' &&
	    methodNode.type !== 'function_expression'
	  ) {
	    methodNode = methodNode.parent;
	  }

	  if (methodNode) {
	    let funcName = null;
	    let funcDefn = methodNode.text;
	    const startLine = methodNode.startPosition.row + 1; // Start line number (1-based)
	    const endLine = methodNode.endPosition.row + 1; // End line number (1-based)

	    // Handle different types of function nodes
	    if (methodNode.type === 'method_definition') {
	      const propertyNode = methodNode.childForFieldName('property');
	      funcName = propertyNode ? propertyNode.text : null; // Capture method name from property
	    } else if (methodNode.type === 'function_declaration') {
	      const nameNode = methodNode.childForFieldName('name');
	      funcName = nameNode ? nameNode.text : null; // Capture function name
	    } else if (methodNode.type === 'arrow_function' || methodNode.type === 'function_expression') {
	      // Arrow functions and function expressions might be assigned to variables
	      const parent = methodNode.parent;

	      if (parent && (parent.type === 'variable_declarator' || parent.type === 'assignment_expression')) {
		const varNameNode = parent.childForFieldName('name');
		funcName = varNameNode ? varNameNode.text : null; // Capture the variable to which the arrow function is assigned
	      }
	    }

	    // Handle function arguments
	    const paramsNode = methodNode.childForFieldName('parameters');
	    const funcArgs = paramsNode ? paramsNode.text : '';

	    return {
	      func_name_: funcName,
	      func_defn_: funcDefn,
	      func_args_: funcArgs,
	      start_line: startLine,
	      end_line: endLine
	    };
	  }

	  return null;
  }

  function extractAssignmentsAndCalls(node, filePath, methodSignature) {
    if (!methodSignature) return;

    let entryKey = `${filePath}#${methodSignature.func_name_}`;
    if (!results[entryKey]) {
      results[entryKey] = [];
    }

    if (node.type === 'assignment_expression') {
      const lhs = node.child(0).text;
      const rhs = node.child(2).text;
      results[entryKey].push({
        Enclosing_Method: methodSignature,
        Assignment: node.text,
        Index: node.startIndex,
        start:  node.startPosition.row + 1,
        endidx: node.endPosition.row + 1
      });
    } else if (node.type === 'call_expression') {
      const funcName = node.child(0).text;
      const args = node.child(1).text;
      results[entryKey].push({
        Enclosing_Method: methodSignature,
        Assignment: node.text,
        Index:  node.startIndex, 
        start:  node.startPosition.row + 1,
        endidx: node.endPosition.row + 1
      });
    }

    for (let i = 0; i < node.childCount; i++) {
      extractAssignmentsAndCalls(node.child(i), filePath, methodSignature);
    }
  }

  function parseTree(node, filePath) {
    let methodSignature = null;
    if ( node.type === 'function_declaration' || node.type === 'method_definition' || node.type === 'arrow_function' || node.type === 'function_expression' ) {
      methodSignature = getEnclosingMethodName(node);
    }

    extractAssignmentsAndCalls(node, filePath, methodSignature);

    for (let i = 0; i < node.childCount; i++) {
      parseTree(node.child(i), filePath);
    }
  }

  parseTree(tree.rootNode, filePath);
  return results;
}

// This function parses the JS file content
function parseUsage(filePath) {

  const code = fs.readFileSync(filePath, 'utf8');
  const tree = parser.parse( code, undefined, options );
  const rootNode = tree.rootNode;

  const variableUsages = {}; // Object to store all imports and their usages

  // Step 1: Find all import statements and capture the LHS variable names
  rootNode.descendantsOfType('variable_declarator').forEach(declNode => {
    const initNode = declNode.childForFieldName('value'); // RHS of the declaration
    const lhsNode = declNode.childForFieldName('name'); // LHS (the variable)

    // Check if the RHS is a `require()` call
    if (initNode && initNode.type === 'call_expression' && initNode.firstChild.text === 'require') {
      const requiredPath = initNode.lastChild.text; // The module being imported
      const importedVariableName = lhsNode ? lhsNode.text : null; // Get the LHS variable name

      if (importedVariableName) {
        // Store the import and initialize the usages array
        variableUsages[ importedVariableName ] = {
          requiredModule: requiredPath,
          usages: [] // We will populate this later with all usages
        };

        console.log(`Captured import: ${importedVariableName} = require(${requiredPath})`);
      }
    }
  });

  // Step 2: Iterate over each imported variable and find its usages
  Object.keys(variableUsages).forEach(importedVariableName => {
    rootNode.descendantsOfType('identifier').forEach(idNode => {
      if (idNode.text === importedVariableName) {
        const parent = idNode.parent;
        const line = idNode.startPosition.row + 1; // Get the line number (1-based)

        // Record the usage and the surrounding context
        const usageContext = parent.text;
	// dont include import statement in usage       
	if ( !parent.text.includes( 'require' ) ){

          variableUsages[ importedVariableName ].usages.push({
            line,
            context: usageContext
          });
          console.log(`Found usage of ${importedVariableName} on line ${line}: ${usageContext}`);
 
	}
      }
    });
  });

  for (const key in variableUsages) {
    const newKey = `${filePath}#${key}`;
    variableUsages[newKey] = variableUsages[key];
    delete variableUsages[key];
  }

  return variableUsages;
}


// Main function to traverse all JS files in the directory and parse them
function traverseAndParseJSFiles(dir) {
  const jsFiles = [];

  // Traverse directory to find all .js files
  function collectJSFiles(directory) {
    const files = fs.readdirSync(directory);
    for (const file of files) {
      const fullPath = path.join(directory, file);
      if (fs.lstatSync(fullPath).isDirectory()) {
        collectJSFiles(fullPath);
      } else if (path.extname(fullPath) === '.js') {
        jsFiles.push(fullPath);
      }
    }
  }

  collectJSFiles(dir);

  // Parse each JS file and collect results
  const allFileDetails = {};
  const usageDetails = {};

  jsFiles.forEach((file) => {
    const result = parseFileDetails(file);
    Object.assign( allFileDetails, result);
  });

  jsFiles.forEach((file) => {
    const result = parseUsage(file);
    Object.assign( usageDetails, result);
  });

  return [allFileDetails, usageDetails];
}

// Directory where your Node.js files are located
const dirPath = './test/';
const [allFileDetails, usageDetails]  = traverseAndParseJSFiles(dirPath);

// Output the results
//console.log(JSON.stringify( usageDetails, null, 2));

function splitAndNormalizeMethodName(methodName) {
  // Split the method name and normalize it by removing any extra characters like `()`, `,`, etc.
  return methodName
    .replace(/[^\w\s]/g, '') // Remove non-alphanumeric characters
    .split(/\s+/) // Split on spaces
    .filter(Boolean) // Remove any empty strings
    .map(word => word.toLowerCase()); // Normalize to lowercase
}

// Function to match file and method name, and return the line number
function findMethodUsage(fileName, methodName) {

  const normalizedFileName = path.basename(fileName, '.js'); // Remove path and .js extension
  const splitMethodName = splitAndNormalizeMethodName(methodName);	

  for (const [key, value] of Object.entries(usageDetails)) {
    const requiredModulePath = value.requiredModule.replace(/[()'"]/g, ''); // Normalize required module path
    const requiredModuleFile = path.basename(requiredModulePath, '.js');

    // Check if the normalized file name matches the required module
    if (normalizedFileName.includes(requiredModuleFile)) {
      console.log(`Match found for file: ${fileName} with required module: ${requiredModulePath}`);

      // Iterate through usages to find the matching method
      for (const usage of value.usages) {

	const contextWords = splitAndNormalizeMethodName(usage.context);

        const foundMatch = splitMethodName.some( element => contextWords[0].includes( element ) );	      
        console.log('GRAZING->', contextWords, splitMethodName, foundMatch);

        //if (usage.context.includes(`${normalizedFileName}.${methodName}`)) {
	if( foundMatch ) {
          console.log(`Method ${methodName} found at line ${usage.line}`);
          return [ key, usage.line] ; // Return the line number of the method usage
        }
      }
    }
  }

  console.log(`No matching method found for file: ${fileName} and method: ${methodName}`);
  return null; // Return null if no match is found
}

[ file_nm, line_num_ ] = findMethodUsage( '/abc/def/upload.controller.js', 'const createPathDir' )
console.log('DUM DUM=>', file_nm, line_num_);

//console.log('FIFI=>', allFileDetails );

function findMatchingKey(dataStructure, inputString, inputIndex) {
  // Step 1: Split the input string based on '#'
  const [inputFilePath, inputMethodName] = inputString.split('#');

  // Step 2: Iterate over the dataStructure
  for (const key in dataStructure) {
    if (Object.hasOwnProperty.call(dataStructure, key)) {
      const [filePath, methodName] = key.split('#');

      // Step 3: Check if the inputFilePath matches the first part of the key
      if (filePath === inputFilePath) {
        const recordsArray = dataStructure[key];

        // Step 4: Iterate through the array of dicts for this key
        for (const record of recordsArray) {
          const startIdx = record.start;
          const endIdx = record.endidx;

          // Step 5: Check if the inputIndex is within the start and end idx
          if (inputIndex >= startIdx && inputIndex <= endIdx) {
            // If a match is found, return the current key (filePath#methodName)
	    console.log('RED DAWN->', methodName, record); 
            return key;
          }
        }
      }
    }
  }

  // If no match is found, return null or a suitable value
  return null;
}

finalOP_ = findMatchingKey( allFileDetails, file_nm, line_num_);
console.log('GOJIRA=>', finalOP_)
