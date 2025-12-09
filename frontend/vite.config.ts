import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    allowedHosts: [
      '.trycloudflare.com'
    ],
    proxy: {
      "/register": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
        timeout: 30000,
        followRedirects: false,
        headers: {
          'Host': 'ingress-nginx-controller.ingress-nginx.svc.cluster.local'
        },
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log(`[PROXY] Proxying ${req.method} ${req.url} to ${options.target}${req.url}`);
            console.log(`[PROXY] Host header:`, proxyReq.getHeader('host'));
            console.log(`[PROXY] Target:`, options.target);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log(`[PROXY] Response ${proxyRes.statusCode} for ${req.url}`);
            console.log(`[PROXY] Response headers:`, proxyRes.headers);
          });
          proxy.on('error', (err, req, _res) => {
            console.error(`[PROXY ERROR] ${err.message} for ${req.url}`);
            console.error(`[PROXY ERROR] errno:`, (err as any).errno);
            console.error(`[PROXY ERROR] code:`, (err as any).code);
            console.error(`[PROXY ERROR] Stack:`, err.stack);
          });
        },
      },
      "/login": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/users": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/edit-user": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/delete-user": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/add-device": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/devices": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/devices/*": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/delete-device": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/edit-device": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/consumptions": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/user": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/user/*": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/admins": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/chat": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/chat/*": {
        target: "http://ingress-nginx-controller.ingress-nginx.svc.cluster.local:80", 
        changeOrigin: true,
        secure: false,
      },
      "/socket.io": {
        target: "http://flask-messages-service.default.svc.cluster.local:5005", 
        changeOrigin: true,
        secure: false,
        ws: true,
      },
    }
  }
})