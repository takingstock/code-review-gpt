from generate_relevant_files import FindRelevantFiles
from python_extractor import PythonASTExtractor
from python_swagger_extract_impl_deets import PythonAPIImplementationDetails

import json

def check_imports( pr_fnm_, pr_method_nm_, py_data_, local_consumers_, global_consumers_ ):
    
    for _key_, line_details_ in py_data_.items():
        ## each element in line_details_ we will have details about every line belonging
        ## to the key which is a combo of "file_nm" and "method name" 
        ## so all we need to do is find if the pr_method is being used in the RHS of an assignment
        curr_fnm_, curr_method_nm_ = _key_.split('#')
        for line_items_ in line_details_:

            if 'RHS' in line_items_ and pr_method_nm_ in line_items_['RHS'] and\
                    curr_fnm_ == pr_fnm_: ## local usage of the method
                        local_consumers_[ curr_fnm_+ line_items_['RHS'] ] = \
                                ( {'file': curr_fnm_, 'calling_line': line_items_['RHS'],\
                                                  'enclosing_method': line_items_['Enclosing_Method'] } )

            elif 'RHS' in line_items_ and pr_method_nm_ in line_items_['RHS'] and\
                    curr_fnm_ != pr_fnm_: ## global usage of the method
                        global_consumers_[ curr_fnm_+ line_items_['RHS'] ] = \
                                ( {'file': curr_fnm_, 'calling_line': line_items_['RHS'],\
                                                  'enclosing_method': line_items_['Enclosing_Method'] } )

def check_api_calls( pr_fnm_, pr_method_nm_, py_data_, py_api_data_,file_list_, local_consumers_, global_consumers_ ):
    '''
    a) find if the pr_method_nm_ defines an api endpoint by scanning py_api_data_
    b) if so, the next step is a bit of a hail mary pass since URLs can be defined in calling methods in many ways
       .. it could be in a config flat file, a json, globally defined in some method , defined in a class and then
       inherited etc
    c) this first iteration will make a simplifying assumption
        1) if the url endpoint is defined within a method, it will add the file + method as a consumer
        2) if the url endpoint is defined globally it will simply add the file + declare scope as global and add 
    d) the idea is to atleast let the dev know that their method change is impacting some files/methods downstream
    '''
    api_endpoint_ = None

    for _key_, api_end_point_ in py_api_data_.items():
        ##below is for better readability
        curr_fnm_, curr_method_nm_ = _key_.split('#')
        if pr_method_nm_ == curr_method_nm_:
            api_endpoint_ = api_end_point_
            break

    if api_endpoint_ == None: return

    ## check if endpoint is being requested inside a method
    global_file_checks_ = [] #this just stores the files that need to be checked for global calls

    for _key_, line_details_ in py_data_.items():
        curr_fnm_, curr_method_nm_ = _key_.split('#')

        if curr_fnm_ == pr_fnm_: continue

        found_ = False
        for line_items_ in line_details_:
            if 'RHS' in line_items_ and api_endpoint_ in line_items_['RHS']:
                global_consumers_[ curr_fnm_ + line_items_['Function Call'] ] = \
                        ( {'file': curr_fnm_, 'calling_line': line_items_['Function Call'],\
                                          'enclosing_method': line_items_['Enclosing_Method'] } )
                found_ = True

        if found_ == False: global_file_checks_.append( _key_ )

    ## check if its being requested inside a file ( meaning a global definition of the url )
    for _key_ in global_file_checks_:
        fnm_ = _key_.split('#')[0]
        with open( fnm_, 'r' ) as fp:
            file_lines_ = fp.readlines()

        for ln_ in file_lines_:
            if api_endpoint_ in ln_:
                global_consumers_[ fnm_ + ln_ ] = \
                        ( {'file': fnm_, 'calling_line': ln_,\
                        'enclosing_method': { 'func_name_': 'NA', 'func_defn_': 'NA' } } )


def generate_py_dependencies( pr_fnm_, pr_method_nm_ ):

    local_consumers_, global_consumers_, swag_extn_, pr_language_ = dict(), dict(), '.yml', '.py'
    ## list all relevant files first .. will scan your entire code base
    ##NOTE-> we will need to add a method to check with the user if they want to 
    ##       skip any folders
    finder_ = FindRelevantFiles( language_extension=pr_language_, swagger_extension=swag_extn_ )
    finder_dict_ = finder_.returnFiles()
    file_list_, yaml_list_ = finder_dict_['lang_files'], finder_dict_['swagger_files']

    ## generate data for all the language specific files
    ## what the below does is to list every file belonging to the specified lang and extract 
    ## all the method details
    py_data_extractor_ = PythonASTExtractor()

    for fnm_ in file_list_:
        py_data_extractor_.extract_from_file( fnm_ )

    py_data_ = py_data_extractor_.data_

    ## generate API end point details since even within the same language we could have 2 different
    ## microservices and hence its best to atleast cover a basic version where if someone were to change
    ## the code in an API endpoint method , lets say "def api_endpoint_...." and this method defines
    ## the endpoint /abc AND we find this API being invoked either in the same microservice or a diff one
    py_api_id = PythonAPIImplementationDetails( yaml_list_, file_list_, py_data_ )
    py_api_id.find_implementing_methods()

    py_api_data_ = py_api_id.api_endpoints_

    ## iterate through all py files and check if the pr_method_nm_ is being invoked in any other file
    ## this should cover cases of package imports
    check_imports( pr_fnm_, pr_method_nm_, py_data_, local_consumers_, global_consumers_ )

    ## check if pr_method_nm_ is actually an API definition and if so , find consumers
    check_api_calls( pr_fnm_, pr_method_nm_, py_data_, py_api_data_, file_list_, local_consumers_, global_consumers_ )

    return local_consumers_, global_consumers_

def generateDownstreamUsages(json_path):

    with open( json_path, 'r' ) as fp:
        js_ = json.load( fp )

    finalResp_ = dict()

    try:
      if 'py' in js_:
        py_arr_ = js_['py']

        for rec_ in py_arr_:
            local_, global_ = generate_py_dependencies( rec_['changed_file'], rec_['method_nm'] )

            finalResp_.update( local_ )
            finalResp_.update( global_ )

    except:
        print('generateDownstreamUsages => py failure', traceback.format_exc())

    return finalResp_

if __name__ == "__main__":

    import time, sys, os
    js_ = generateDownstreamUsages( os.getenv('ROOT_CHANGES_JSON') )
    with open( os.getenv('PY_DOWNSTREAM_USAGE'), 'w' ) as fp:
        json.dump( js_, fp, indent=2 )
