# Redesigned Pakon

Redesigned Pakon, abbreviated as rePakon, is a tool that provides statistics and usage about your Internet traffic.

There is a dashboard where you can find details like which device (recognized by MAC address and hostname) in your local network attempted to connect to specific websites. It lets users know which protocol was used while reaching the server. Also, it provides them if the connection was secured or not and how long the connection lasted. Users might as well appreciate knowing how much data was received and sent by the server.

It helps to identify any malicious traffic in your network and see if the usage of your network is under good circumstances and rules to keep you safe.

## Dependencies

This project uses Tailwind CSS as the framework and React JS as the library. Both these technologies aim to provide a responsible and modern user interface with a good user experience. They can be installed by npm.

## Development

You can run the app locally to fiddle around it, improve it, add new things, or remove some things while debugging for development purposes.

### `npm start`

This command starts the development mode for your application with the internal webserver. If everything is working, it opens the web browser and takes you to the application available on your computer at this address [http://localhost:3000](http://localhost:3000)

If you make any changes in the source code, the website will reload automatically, and you can see any lint errors in the console.

## Deployment

In production, you want to have production files optimized for the best performance instead of being large, which provides helpful ways for developers to improve their source code.

### `npm run build`

This command optimizes and builds the source code for the production. We can see how much the files were reduced in the console and when the build system assumed where the website should be hosted.

Production files, we can see in the build folder, which was created by this process.

### Lighttpd configuration

If you deploy this application to the router, which uses the Lighttpd web server, by default, be sure that in the folder `/etc/lighttpd/conf.d/`, there is `repakon.conf` with the following content:

```
alias.url += ( "/repakon/" => "/www/repakon/")

$HTTP["url"] =~ "^/repakon$" {
    url.redirect = ( "^/repakon$" => "/repakon/" )
}
```

This provides configuration for the Lighttpd web server, where can be found files on the router to be served to users and there is also redirect.