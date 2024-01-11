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

  fetch(loginUrl, loginOptions)
    .then(response => {
      if (response.status === 200){
          alert('Книга успішно видалена з Вашого профілю.');
          window.location.href = '/profile';
      }
    });
}