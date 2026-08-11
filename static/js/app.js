// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        document.querySelectorAll('.alert-dismissible').forEach(function(el) {
            var alert = bootstrap.Alert.getOrCreateInstance(el);
            alert.close();
        });
    }, 5000);
});
