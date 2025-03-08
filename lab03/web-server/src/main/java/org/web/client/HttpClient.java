package org.web.client;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.PrintWriter;
import java.net.Socket;

public class HttpClient {
    public static void main(String[] args) {
        if (args.length != 3) {
            System.out.println("Usage: java HttpClient <server_host> <server_port> <filename>");
            return;
        }

        String serverHost = args[0];
        String fileName = args[2];
        int serverPort;
        try {
            serverPort = Integer.parseInt(args[1]);
        } catch (NumberFormatException e) {
            System.out.println("Error: Port must be an integer");
            return;
        }

        try (Socket socket = new Socket(serverHost, serverPort);
             PrintWriter out = new PrintWriter(socket.getOutputStream(), true);
             BufferedReader in = new BufferedReader(new InputStreamReader(socket.getInputStream()))) {
            out.println("GET /" + fileName + " HTTP/1.1\r\n");
            out.println("Host: " + serverHost + "\r\n");
            out.print("\r\n");
            out.println();

            String line;
            System.out.println("Server response:");
            while ((line = in.readLine()) != null) {
                System.out.println(line);
            }
        } catch (IOException e) {
            System.out.println("Error connecting to server: " + e.getMessage());
        }
    }
}
