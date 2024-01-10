const SimpleSearchForLiterature = () => {
    const searchInputValue = document.getElementById("book_id").value;
    window.location.href = `/library/${searchInputValue}/`;
        }

const searchForWeather = () => {
    const searchInputValue = document.getElementById("city_id").value;
    window.location.href = `/weather/${searchInputValue}/`;
        }

