using System.Collections.Generic;
using Data;
using Proyecto26; // Importing the RestClient library
using Utilities;

/// <summary>
/// Provides static methods for sending REST requests.
/// </summary>
public static class Rest
{
    // ReSharper disable Unity.PerformanceAnalysis
    /// <summary>
    /// Sends a POST request with a base64-encoded image and handles the response.
    /// </summary>
    public static void PostBase64(string image, LogData logData, FerHandler ferHandler)
    {
        // Create a new HTTP request for sending a base64 image
        RequestHelper currentRequest = CreateBase64RequestHelper(image);
        
        // Make a POST request and handle the response or error
        RestClient.Post(currentRequest)
            .Then(response => ferHandler.ProcessRestResponse(response.Text, logData))  // Process the response if request is successful
            .Catch(error => ferHandler.ProcessRestError(error, logData));  // Process the error if request fails
    }

    /// <summary>
    /// Creates and configures a RequestHelper object for sending a base64-encoded image.
    /// </summary>
    /// <param name="image">The base64-encoded image string.</param>
    /// <returns>A configured RequestHelper object for making the HTTP request.</returns>
    private static RequestHelper CreateBase64RequestHelper(string image)
    {
        // Construct and return a RequestHelper object
        return new RequestHelper
        {
            Uri = EditorUI.EditorUI.Instance.RestBasePath + "recognize/base64", // Set the URI for the REST endpoint
            Headers = new Dictionary<string, string> { { "accept", "application/json" } }, // Set the HTTP headers
            ContentType = "text/plain", // Set the content type of the request body
            BodyString = image, // Set the base64-encoded image as the request body
            EnableDebug = false, // Disable debug logging for the request
            Timeout = 1 // Set the timeout duration for the request
        };
    }
}