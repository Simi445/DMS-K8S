import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Link } from "react-router-dom"
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { useForm } from "react-hook-form";
import { useEffect, useState } from "react"
export function LoginForm({
  className,
  onTokenUpdate,
  ...props
}) {

  const [error, setError] = useState('');

  useEffect(() => {
        let timer: number | undefined
        
        if (error) {
          timer = setTimeout(() => {
            setError('')
          }, 1000)
        }
        
        return () => {
          if (timer) clearTimeout(timer)
        }
      }, [error])

      
  const form = useForm({
      defaultValues: {
      username: '',
      password: '',
    }
  });

  const login= async(props)=>
  {
  {
    try {
          const response = await fetch("/login", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(props),
          });
    
          const data = await response.json();
          if (data.error) {
            setError(data.error);
          }
          else {
          form.reset();
          onTokenUpdate(data.token)
          }
        } 
        catch (error) {
          return ("Error:" + error);
        }
  }
}

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      {error && (
                <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded w-full">
                  {error}
                </div>
              )}
      <Card>
        <CardHeader>
          <CardTitle>Login to your account</CardTitle>
          <CardDescription>
            Enter your email below to login to your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(login)} className="flex flex-col gap-6">
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel htmlFor="username">Username</FormLabel>
                    <FormControl>
                      <Input id="username" type="text" placeholder="Your username" {...field} required />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel htmlFor="password">Password</FormLabel>
                    <FormControl>
                      <Input id="password" type="password" placeholder="Your password" {...field} required />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex flex-col gap-3">
                <Button type="submit" className="w-full">
                  Login
                </Button>
              </div>
              <div className="mt-4 text-center text-sm">
                Don't have an account?{" "}
                <Link to = "/register" className="underline underline-offset-4">
                  Register
                </Link>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  )
}
