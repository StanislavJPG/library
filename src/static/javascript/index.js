const fileInput = document.querySelector('#file');

fileInput.addEventListener('change', async function () {
    const chosenFile = this.files[0];

    if (chosenFile) {
        const formData = new FormData();
        formData.append('file', chosenFile);

        try {
            const response = await fetch('/image', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const responseData = await response.json();
                if (responseData.status === 200) {
                    alert('Зміни збережено');
                    location.reload();
                } else {
                    alert('Помилка збереження.');
                }
            }
        } catch (error) {
            console.error('Error:', error);
        }
    }
});


function deleteBook(book_id) {
    console.log(book_id);
  const loginUrl = `/api/books/${book_id}`;
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
              location.reload();
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
