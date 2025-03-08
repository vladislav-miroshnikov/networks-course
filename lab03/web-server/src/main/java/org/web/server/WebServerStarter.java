package org.web.server;

import java.io.File;
import java.io.IOException;

public class WebServerStarter {
    public static void main(String[] args) {
        if (args.length != 2) {
            System.out.println("Usage: java WebServerStarter <server_port> <concurrency_level>");
            return;
        }

        try {
            int port = Integer.parseInt(args[0]);
            int concurrencyLevel = Integer.parseInt(args[1]);
            if (port <= 0 || concurrencyLevel <= 0) {
                System.out.println("Error: Port or Concurrency level must be positive");
                return;
            }
            File rootDir = new File(WebServer.FILES_DIR);
            if (!rootDir.exists()) {
                rootDir.mkdir();
            }
            WebServer server = new WebServer(port, concurrencyLevel);
            server.start();
        } catch (NumberFormatException e) {
            System.out.println("Error: Port and concurrency level must be integers");
        } catch (IOException e) {
            System.out.println("Could not start web server, reason: " + e.getMessage());
        }
    }
}