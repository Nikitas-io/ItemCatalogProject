window.fbAsyncInit = function() {
  FB.init({
    appId: "346853069242004", // My App ID.
    cookie: true, // Enable cookies to allow the server to access the session.
    xfbml: true, // Parse social plugins on this page.
    version: "v2.2" // Use version 2.2
  });
};

// Load the SDK asynchronously.
(function(d, s, id) {
  let js,
    fjs = d.getElementsByTagName(s)[0];
  if (d.getElementById(id)) return;
  js = d.createElement(s);
  js.id = id;
  js.src = "//connect.facebook.net/en_US/sdk.js";
  fjs.parentNode.insertBefore(js, fjs);
})(document, "script", "facebook-jssdk");

// Here we run a very simple test of the Graph API after login is
// successful.  See statusChangeCallback() for when this call is made.
function sendTokenToServer() {
  let access_token = FB.getAuthResponse()["accessToken"];
  console.log(access_token);
  console.log("Welcome!  Fetching your information.... ");
  // Showing that we can also use the FB SDK to also make API calls.
  FB.api("/me", function(response) {
    console.log("Successful login for: " + response.name);
    // Get the session's state from the login tamplate.
    let sessionState = $("#googleSigninButton").attr("data-state");
    // Send the access_token to the sever via Ajax along with the state value.
    // We'll name the route fbconnect, which we'll implement on the client-side.
    $.ajax({
      type: "POST",
      url: "/fbconnect?state=" + sessionState,
      processData: false,
      data: access_token,
      contentType: "application/octet-stream; charset=utf-8",
      success: function(result) {
        // Handle or verify the server response if necessary.
        if (result) {
          $("#result").html(
            "Login Successful!</br>" + result + "</br>Redirecting..."
          );
          setTimeout(function() {
            window.location.href = "/home";
          }, 4000);
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
  });
}
