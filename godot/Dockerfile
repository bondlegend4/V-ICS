FROM nginx:alpine

# Copy your HTML5 export into the nginx html directory
COPY export/ /usr/share/nginx/html/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]