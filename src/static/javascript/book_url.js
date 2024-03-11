const SimpleSearchForLiterature = () => {
    const searchInputValue = document.getElementById("book_id").value;
    window.location.href = `/library/${searchInputValue}/`;
        }
