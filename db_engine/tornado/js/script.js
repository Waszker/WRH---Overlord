/**
* Sends request to specified host on specified port and returns its response.
* Can be used when controlling some devices.
*/
function getRequest(module_class, message, callback_function) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function()
    {
        if(xmlHttp.readyState == 4 && xmlHttp.status == 200)
        callback_function(xmlHttp.responseText)
    };
    xmlHttp.open("GET", "request?class=" + module_class + "&message=" + message, true);
    xmlHttp.send();
}

/**
* Sends POST request to specified host on specified port and returns its response.
* Can be used when controlling some devices.
* Better than the getRequest function because POST requests don't have size limits.
*/
function postRequest(module_class, message, callbackFunction) {
    var http = new XMLHttpRequest();
    http.onreadystatechange = function() {
        if(http.readyState == 4 && http.status == 200 && callbackFunction != null) {
            callbackFunction(http.responseText);
        }
    };
    http.open("POST", "request?class=" + module_class + "&message=" + message, true);
    http.send();
}