const literatureValue = window.location.pathname.split('/').pop();

document.querySelectorAll('.saveButton').forEach(button => {
    button.addEventListener('click', () => {
        const bookIndex = button.getAttribute('data-book-index');

        let isSave = confirm('Ви бажаєте зберегти цю книгу до Вашого профілю?');
        if (isSave) {
            alert('Зачекайте, книга зберігається до вашого профілю...');
            fetch(`/api/library/save_book/${literatureValue}?num=${bookIndex}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}),
            })
            .then(response => {
                if (response.status === 200) {
                    alert('Книгу успішно збережено.');
                    location.reload();
                } else if (response.status === 401) {
                    alert('Помилка\nВам необхідно авторизуйтись, щоб зберегти книгу до профілю.');
                } else if (response.status === 409) {
                    alert('Помилка\nЦя книга вже збережена до вашого профілю!');
                }
            })
            .catch(error => {
                alert('Помилка збереження книги.');
            });
            const currentURL = window.location.href;
            getURL(currentURL);
        }
    });
});


document.querySelectorAll('.Button').forEach(button => {
    button.addEventListener('click', () => {
        var isOpen = confirm('Ви хочете відкрити книжку у новій вкладці?');
        if (isOpen) {
            let temp = window.open(button.getAttribute('id'));
        }
    });
});


const booksValue = window.location.pathname.split('/').pop();
document.querySelectorAll('.readButton').forEach(button => {
    button.addEventListener('click', () => {

        const url = `/read/${booksValue}?num=1`;
        window.open(url, '_blank');
    });
});

function saveBookFromProfile(book_id) {
    console.log(book_id);
  const saveUrl = `/api/save_back/${book_id}`;
  const saveOptions = {
    method: 'PUT',
    headers: {
      'accept': 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  };

    var isSave = confirm('Зберегти цю книгу до Вашого профілю?');
    if (isSave) {
      fetch(saveUrl, saveOptions)
        .then(response => {
          if (response.status === 200){
              location.reload();
          }
      })
    };
}
