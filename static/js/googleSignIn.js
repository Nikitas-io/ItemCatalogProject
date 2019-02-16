// Takes in an Auth result object as input.
function signInCallback(authResult) {
  // If the Auth object contains a 'code' parameter, then we know
  // that the authorization with the Google API server was successful,
  // and our one-time-use code is present.
  if (authResult["code"]) {
    // Hide the sign-in button now that the user is authorized.
    $("#googleSigninButton").attr("style", "display: none");
    // Get the session's state from the login tamplate.
    let sessionState = $("#googleSigninButton").attr("data-state");
    // Send the one-time-use code to the server, if the server responds,
    // write a 'login successful' message to the web page and then redirect
    // back to the home page.
    $.ajax({
      type: "POST",
      // To the GConnect method, we pass the login_session's state
      // token as an argument to verify against cross-site
      // reference forgery attacks.
      url: "/gconnect?state=" + sessionState,
      // Setting processData to false indicates that we don't want
      // jQuery to process the response into a string.
      processData: false,
      // This application/octet-stream indicates that we are sending an
      // arbitrary binary stream of data.
      contentType: "application/octet-stream; charset=utf-8",
      // Here we specify the data that we'll send along to our server,
      // the one-time-use code.
      data: authResult["code"],
      // In case the response is successful:
      success: function(outputMessage) {
        // Handle or verify the server response if necessary.
        if (outputMessage) {
          $("#result").html(
            "Login was successful: " +
              outputMessage +
              "</br>Redirecting to home page..."
          );
          setTimeout(function() {
            window.location.href = "/home";
          }, 4000);
          // Error response handling for the console.
        } else if (authResult["error"]) {
          console.log("There was an error: " + authResult["error"]);
          // No response handling.
        } else {
          $("#result").html(
            "Failed to make a server-side call. Check your configuration and console."
          );
        }
      },
      fail: function(xhr, textStatus, errorThrown) {
        alert("The request has failed. Here's some info about that: " + errorThrown + ", " + textStatus + ".");
      }
    });
  }
}
