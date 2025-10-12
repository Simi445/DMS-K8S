import React, { useContext, useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from "@/components/ui/form";
import { Link } from "react-router-dom";


export function Register({ onTokenUpdate }: { onTokenUpdate: (token: string) => void }) {
  const [error, setError] = useState('');
  const form = useForm({
    defaultValues: {
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    role: ''
  }
});


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

  const register = async (props: { [x: string]: any; username?: string; email?: string; password?: any; confirm_password: any; role?: string; })=>
  {
    setError('');
    if (props.password !== props.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    const {confirm_password, ...dataToSend} = props
    try {
          const response = await fetch("/register", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify(dataToSend),
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

  return (
    <div className={cn("flex flex-col gap-6 items-center justify-center w-full max-w-md h-[41.5rem]")}>
      {error && (
                <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded w-full">
                  {error}
                </div>
              )}
      <Card className="w-full h-full flex flex-col justify-between">
        <CardHeader className="text-center">
          <CardTitle>Create a new account</CardTitle>
          <CardDescription style={{ marginTop: '14%' }}> 
            Enter your details below to create a new account
          </CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col justify-center">
          <Form {...form}>
            <form onSubmit={form.handleSubmit((p)=>register(p))} className="flex flex-col gap-6">
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
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel htmlFor="email">Email</FormLabel>
                    <FormControl>
                      <Input id="email" type="email" placeholder="example@example.com" {...field} required />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
              control={form.control}
              name="role"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Role</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a role" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="user">User</SelectItem>
                      <SelectItem value="admin">Admin</SelectItem>
                    </SelectContent>
                  </Select>
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
              <FormField
                control={form.control}
                name="confirm_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel htmlFor="confirm_password">Confirm Password</FormLabel>
                    <FormControl>
                      <Input id="confirm_password" type="password" placeholder="Your password" {...field} required />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex flex-col gap-3">
                <Button type="submit" className="w-full">
                  Register
                </Button>
              </div>
              <div className="mt-4 text-center text-sm">
                Already have an account?{" "}
                <Link to = "/login" className="underline underline-offset-4">
                  Login
                </Link>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}

export default Register;