function addNewUser() {
  var email = $('#newUserEmail').val();
  var imageUrl = $('#newUserImageURL').val();
  var nickname = $('#newUserNickname').val();
  var accessToken = 'token_' + Math.random().toString(36).substr(2, 9);
  var providerId = 'google_' + Math.random().toString(36).substr(2, 9);

  $.ajax({
    url: 'http://localhost:8000/add_new_user',
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({
      access_token: accessToken,
      email: email,
      provider: 'google',
      provider_id: providerId,
      image: imageUrl,
      nickname: nickname
    }),
    success: function(response) {
      $('#response')
          .html('User added successfully: ' + JSON.stringify(response));
    },
    error: function(response) {
      $('#response').html('Error adding user: ' + response.responseText);
    }
  });
}

$(document).ready(function() {
  $('#addUserButton').click(addNewUser);
});

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
      $('#response').html(JSON.stringify(response));
    },
    error: function(error) {
      $('#response').html('Error: ' + error.responseText);
    }
  });
}

$('#loginButton').click(function() {
  var userId = $('#userId').val();
  var testToken = 'mockToken_' + userId;

  $.ajax({
    url: 'http://localhost:8000/verify_token',
    type: 'POST',
    contentType: 'application/json',
    data: JSON.stringify({token: testToken}),
    success: function(response) {
      sessionStorage.setItem('mockToken', testToken);
      showApiTestSection();
      getUserProfile();
    },
    error: function(response) {
      alert('Login failed: ' + response.responseText);
    }
  });
});

function searchUser(nickname) {
  var token = sessionStorage.getItem('mockToken');
  if (!token) {
    $('#response').html('Error: No token found. Please login first.');
    return;
  }

  $.ajax({
    url: 'http://localhost:8000/get_user_by_nickname?nickname=' +
        encodeURIComponent(nickname),
    type: 'GET',
    headers: {'Authorization': 'Bearer ' + token},
    success: function(response) {
      $('#response').html(JSON.stringify(response));
      friendUserId = response.user_id;  // Assuming response contains user_id
      $('#addFriendButton').show();
    },
    error: function(response) {
      $('#response').html('Error: ' + response.responseText);
    }
  });
}

function sendFriendRequest() {
  var token = sessionStorage.getItem('mockToken');
  if (!token) {
    $('#response').html('Error: No token found. Please login first.');
    return;
  }

  $.ajax({
    url: 'http://localhost:8000/add_friend?nickname=' +
        encodeURIComponent(friendUserId),
    type: 'POST',
    headers: {'Authorization': 'Bearer ' + token},
    success: function(response) {
      $('#response').html('Friend request sent: ' + JSON.stringify(response));
    },
    error: function(error) {
      $('#response').html('Error: ' + JSON.stringify(error.responseJSON));
    }
  });
}

function friendList() {
  var token = sessionStorage.getItem('mockToken');
  if (!token) {
    $('#response').html('Error: No token found. Please login first.');
    return;
  }

  $.ajax({
    url: 'http://localhost:8000/get_friend_pending_list',
    type: 'GET',
    headers: {'Authorization': 'Bearer ' + token},
    success: function(response) {
      $('#response').html(JSON.stringify(response));
    },
    error: function(response) {
      $('#response').html('Error: ' + response.responseText);
    }
  });
}



$(document).ready(function() {
  $('#getUserProfile').click(function() {
    getUserProfile();
  });

  $('#UpdateImage').click(function() {
    var newImageUrl = $('#newImageUrl').val();
    var token = sessionStorage.getItem('mockToken');

    if (!token) {
      $('#response').html('Error: No token found. Please login first.');
      return;
    }

    $.ajax({
      url: 'http://localhost:8000/update_image',
      type: 'PUT',
      contentType: 'application/json',
      headers: {'Authorization': 'Bearer ' + token},
      data: JSON.stringify({image: newImageUrl}),
      success: function(response) {
        $('#response').html(JSON.stringify(response));
      },
      error: function(response) {
        $('#response').html('Error: ' + response.responseText);
      }
    });
  });

  $('#searchButton').click(function() {
    var nickname = $('#search').val();
    searchUser(nickname);
  });

  $('#addUserButton').click(addNewUser);
  $('#addFriendButton').click(sendFriendRequest);
  $('#getFriendListButton').click(friendList);
});