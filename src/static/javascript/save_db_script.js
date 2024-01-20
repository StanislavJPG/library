const literatureValue = window.location.pathname.split('/').pop();

document.querySelectorAll('.saveButton').forEach(button => {
    button.addEventListener('click', () => {
        const bookIndex = button.getAttribute('data-book-index');


        let isSave = confirm('Ви бажаєте зберегти цю книгу до Вашого профілю?');
        if (isSave) {
            alert('Зачекайте, книга зберігається до вашого профілю...');
            fetch(`/library/save_book/${literatureValue}?num=${bookIndex}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({}),
            })
            .then(response => {
                if (response.status === 200) {
                    alert('Книгу успішно збережено.');
                } else if (response.status === 401) {
                    alert('Помилка\nВам необхідно авторизуйтись, щоб зберегти книгу до профілю.');
                } else if (response.status === 409) {
                    alert('Помилка\nЦя книга вже збережена до вашого профілю!');
                }
            })
            .catch(error => {
                alert('Помилка збереження книги.');
            });
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