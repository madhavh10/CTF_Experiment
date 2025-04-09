FROM php:8.2-apache

COPY index.php /var/www/html/index.php
COPY flag.txt /flag.txt

# Permissions (deny browser access directly via web root)
RUN chmod 644 /flag.txt && chown www-data:www-data /flag.txt

EXPOSE 80