package org.web.server;

import java.io.*;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.file.Files;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class WebServer {
    public static final String FILES_DIR = "./webroot_dir";
    private final ServerSocket serverSocket;
    private final ExecutorService threadPool;

    public WebServer(int port, int concurrencyLevel) throws IOException {
        serverSocket = new ServerSocket(port);
        threadPool = Executors.newFixedThreadPool(concurrencyLevel);
        System.out.println("WebServer has started on port: " + port);
    }

    public void start() {
        try {
            while (true) {
                Socket clientSocket = serverSocket.accept();
                System.out.println("New client connection accepted: " + clientSocket.getInetAddress());
                threadPool.submit(() -> {
                    try {
                        handleClientRequest(clientSocket);
                    } catch (IOException e) {
                        System.err.println("Error handling client: " + e.getMessage());
                    } finally {
                        try {
                            clientSocket.close();
                        } catch (IOException e) {
                            System.err.println("Error closing client socket: " + e.getMessage());
                        }
                    }
                });
            }
        } catch (IOException e) {
            System.err.println("WebServer error: " + e.getMessage());
        } finally {
            threadPool.shutdown();
        }
    }

    private void handleClientRequest(Socket clientSocket) throws IOException {
        try (BufferedReader in = new BufferedReader(new InputStreamReader(clientSocket.getInputStream()));
             PrintWriter out = new PrintWriter(clientSocket.getOutputStream());
             BufferedOutputStream dataOut = new BufferedOutputStream(clientSocket.getOutputStream())) {
            String requestLine;
            try {
                requestLine = in.readLine();
            } catch (IOException e) {
                System.err.println("Error reading client request: " + e.getMessage());
                return;
            }

            if (requestLine == null) {
                return;
            }
            System.out.println("Request: " + requestLine);

            String[] tokens = requestLine.split(" ");
            if (tokens.length < 2 || !tokens[0].equals("GET")) {
                return;
            }

            String filePath = tokens[1];
            if (filePath.equals("/")) {
                filePath = "/index.html";
            }

            File file = new File(FILES_DIR + filePath);
            if (file.exists() && !file.isDirectory()) {
                byte[] fileData = Files.readAllBytes(file.toPath());
                out.print("HTTP/1.1 200 OK\r\n");
                out.print("Content-Type: " + getContentType(filePath) + "\r\n");
                out.print("Content-Length: " + fileData.length + "\r\n");
                out.print("\r\n");
                out.flush();
                dataOut.write(fileData, 0, fileData.length);
                dataOut.flush();
            } else {
                String errorMessage = "404 Not Found";
                out.print("HTTP/1.1 404 Not Found\r\n");
                out.print("Content-Type: text/plain\r\n");
                out.print("Content-Length: " + errorMessage.length() + "\r\n");
                out.print("\r\n");
                out.print(errorMessage);
                out.flush();
            }
        }
    }

    private String getContentType(String path) {
        if (path.endsWith(".html")) {
            return "text/html";
        }
        if (path.endsWith(".txt")) {
            return "text/plain";
        }
        if (path.endsWith(".jpg") || path.endsWith(".jpeg")) {
            return "image/jpeg";
        }
        if (path.endsWith(".png")) {
            return "image/png";
        }
        return "application/octet-stream";
    }
}
