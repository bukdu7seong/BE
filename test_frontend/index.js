function showApiTestSection() {
  $('#apiTestSection').show();
}

function getUserProfile() {
  var token = sessionStorage.getItem('mockToken');
  if (!token) {
    alert('No token found. Please login first.');
    return;
  }
  $.ajax({
    url: 'http://localhost:8000/profile',
    type: 'GET',
    headers: {'Authorization': 'Bearer ' + token},
    success: function(response) {
      var img = $('<img>', {src: response.image});
      console.log(response);
      $('#response').html(img);
    },
    error: function(error) {
      console.log(error);
      $('#response').html('Error: ' + error.responseText);
    }
  });
}

function loginUser() {
  var userId = $('#userId').val();
  var testToken = 'mockToken_' + userId;

  $.ajax({
    url: 'http://localhost:8000/login',
    type: 'GET',
    contentType: 'application/json',
    headers: {'Authorization': 'Bearer ' + testToken},
    success: function(response) {
      sessionStorage.setItem('mockToken', testToken);
      showApiTestSection();
      getUserProfile();
    },
    error: function(response) {
      alert('Login failed: ' + response.responseText);
    }
  });
}

function addNewUser() {
  var email = $('#newUserEmail').val();
  var nickname = $('#newUserNickname').val();
  var accessToken = 'token_' + Math.random().toString(36).substr(2, 9);
  var providerId = 'google_' + Math.random().toString(36).substr(2, 9);

  var reader = new FileReader();
  reader.onload = function(e) {
    var base64Image = e.target.result;
    var img = $('<img>', {src: base64Image});
    $('#response').html(img);

    $.ajax({
      url: 'http://localhost:8000/add_new_user',
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({
        email: email,
        image: base64Image,
        nickname: nickname,
        access_token: accessToken,
        provider_id: providerId
      }),
      success: function(response) {
        $('#response')
            .html('User added successfully: ' + JSON.stringify(response));
      },
      error: function(response) {
        $('#response').html('Error adding user: ' + response.responseText);
      }
    });
  };
  reader.readAsDataURL($('#newUserImage')[0].files[0]);
}


$(document).ready(function() {
  $('#addUserButton').click(addNewUser);
});

// events

$('#loginButton').click(loginUser);
