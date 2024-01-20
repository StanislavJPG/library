    const img = document.querySelector('#photo');
    const file = document.querySelector('#file');

    file.addEventListener('change', function () {
        const chosenFile = this.files[0];
        if (chosenFile) {
            const formData = new FormData();
            formData.append('image', chosenFile);

            fetch('/image', {
                method: 'PATCH',
                body: formData,
            })
            .then(response => response.json())
            .then(data => {
                if (data.Success === 200) {
                    img.setAttribute('src', URL.createObjectURL(chosenFile));
                }
            })
            .catch(error => console.error('Error:', error));
        }
    });


function deleteBook(book_title) {
    console.log(book_title);
  const loginUrl = `/books/${book_title}`;
  const loginOptions = {
    method: 'DELETE',
    headers: {
      'accept': 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  };

    var isDelete = confirm('Видалити цю книгу з профілю?');
    if (isDelete) {
      fetch(loginUrl, loginOptions)
        .then(response => {
          if (response.status === 200){
              alert('Книга успішно видалена з Вашого профілю.');
              window.location.href = '/profile';
          }
      })
    };
}

function sendVerificationEmail(email) {
  var isSend = confirm('Відправити код підтвердження Вам на пошту?')
  if (isSend) {
      const requestURL = '/auth/request-verify-token';
      const data = {"email": email};
      const Options = {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      };

      fetch(requestURL, Options)
        .then(response => {
          if (response.status !== 202){
              alert('Помилка підтвердження.')
          }
      })
    }
    };

document.addEventListener('DOMContentLoaded', function () {
    var showPopupButton = document.getElementById('showPopupButton');
    var popupContainer = document.getElementById('popupContainer');
    var closePopup = document.getElementById('closePopup');

    showPopupButton.addEventListener('click', function () {
        popupContainer.style.display = 'block';
    });

    closePopup.addEventListener('click', function () {
        popupContainer.style.display = 'none';
    });

    window.addEventListener('click', function (event) {
        if (event.target === popupContainer) {
            popupContainer.style.display = 'none';
        }
    });
});

function acceptVerificationEmail(token) {
  const requestURL = '/auth/verify';
  const data = {"token": token};
  const Options = {
    method: 'POST',
    headers: {
      'accept': 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  };

  fetch(requestURL, Options)
    .then(response => {
      if (response.status === 200){
          window.location.href = '/profile';
          alert('Ви підтвердили Ваш профіль.');
      } else {
        alert('Помилка перевірки коду.')
      };

  })
}
