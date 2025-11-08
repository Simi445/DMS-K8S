import { useEffect, useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import { LoginForm } from './components/login-form'
import {Register} from './Register'
import Home from './main-page'
import { jwtDecode } from "jwt-decode";
import { BrowserRouter, Routes, Route, Link, Navigate } from 'react-router-dom';
import type { JWTPayload } from "@/lib/types"

function App() {
  const [count, setCount] = useState(0)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [role, setRole] = useState('')
  const [username, setUername] = useState('')
  const [currentUserAuthId, setCurrentUserAuthId] = useState<number | null>(null)

  useEffect(() => {
      let timer: number | undefined
      let decoded: JWTPayload | undefined;
      if (token) {
        decoded = jwtDecode<JWTPayload>(token);
        if (decoded) {
          const decodedUsername = decoded.username ?? ''
          setUername(decodedUsername)
          
          if (decoded.auth_id) {
            fetch(`/users`, {
              headers: {
                "Authorization": `Bearer ${token}`
              }
            })
              .then(response => response.json())
              .then(data => {
                const users = data.users || []
                const user = users.find((u: any) => u.username === decodedUsername)
                if (user) {
                  setRole(user.role ?? '')
                  setUername(user.username ?? '')
                  setCurrentUserAuthId(user.auth_id ?? null)
                } else {
                  setRole('')
                  setUername(decodedUsername)
                  setCurrentUserAuthId(null)
                }
              })
              .catch(error => {
                console.error('Failed to fetch user details:', error)
                setRole('')
                setUername(decodedUsername)
              })
          }
          
          if (decoded.exp && (decoded.exp * 1000) <= Date.now()) 
          {
              setToken(null)
              localStorage.removeItem('token')
              return;
          }
          
          
          if (decoded.exp) {
            timer = setTimeout(() => {
              setToken(null)
              localStorage.removeItem('token')
            }, (decoded.exp * 1000) - Date.now())
          }
        }
      }
      
      return () => {
        if (timer) clearTimeout(timer)
      }
    }, [token])
  
  const handleTokenUpdate = (newToken: string) => {
    localStorage.setItem('token', newToken)
    setToken(newToken)
  }

  const handleLogout = () => {
    setToken(null)
    localStorage.removeItem('token')
  }

  function MainComponent({ children }: React.PropsWithChildren<{}>) 
  {
    return(
      <div className="flex items-center justify-center min-h-screen">
      <div className="w-full max-w-md">
        {children}
      </div>
    </div>
    )
  }

  return (
    <BrowserRouter>
    <Routes>
        <Route path="/" element={token ? <Home handleLogout={handleLogout} role={role} username={username} currentUserAuthId={currentUserAuthId}/> : <Navigate to="/login" replace />} />
        <Route path="/register" element={!token ? <MainComponent><Register onTokenUpdate={handleTokenUpdate}/></MainComponent> : <Navigate to="/" replace />} />
        <Route path="/login" element={!token ?  <MainComponent><LoginForm onTokenUpdate={handleTokenUpdate} className={undefined}/> </MainComponent>: <Navigate to="/" replace />}/>
    </Routes>
    </BrowserRouter>
  )
}

export default App
