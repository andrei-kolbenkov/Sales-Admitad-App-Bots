// Показываем содержимое и скрываем загрузчик, когда страница полностью загружена
window.addEventListener("load", function () {
    const loader = document.getElementById("loader");
    const content = document.getElementById("content");

    if (loader) {
        loader.style.display = "none"; // Скрываем загрузчик
    }
    if (content) {
        content.style.display = "block"; // Показываем содержимое
    }
});
