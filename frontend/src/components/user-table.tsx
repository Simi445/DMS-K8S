import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useEffect, useState } from "react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "./ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"
import { Link } from "react-router-dom"
import { set } from "react-hook-form"


export function UserTable({userForm, users  , setUsers, getUsers, currentUserAuthId}) {

  function UserEdit({userId}: {userId: number})
  {
    const currentUser = users.find((user) => user.auth_id === userId);
    const handleDialogOpen = () => {
      if (currentUser) {
        const userDataMap = {
          username: currentUser.username,
          email: currentUser.email,
          password: '',
          role: currentUser.role
        };
        
        for (const [key, value] of Object.entries(userDataMap)) {
          userForm.setValue(key, value);
        }
      }
    };

    const onSubmit = async (data: any) => {
      try {
          const dataSend = {"auth_id": userId, ...data}
          const response = await fetch("/edit-user", {
            method: "PUT",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(dataSend),
          });
    
          const data_resp = await response.json();
          if (data_resp.error) {
            console.log(data_resp.error);
            return;
          }
          getUsers();
        } 
        catch (error) {
          return ("Error:" + error);
        }
    };

    return (<Dialog>
          <DialogTrigger asChild>
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleDialogOpen}
            >
              Edit
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Edit data:</DialogTitle>
              <DialogDescription>
                Fill in the form below to edit user data.
              </DialogDescription>
            </DialogHeader>
          <Form {...userForm}>
            <form onSubmit={userForm.handleSubmit(onSubmit)} className="flex flex-col gap-6">
              <FormField
                control={userForm.control}
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
                control={userForm.control}
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
              control={userForm.control}
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
              <div className="flex flex-col gap-3">
                <Button type="submit" className="w-full">
                  Edit User
                </Button>
              </div>
            </form>
          </Form>
          </DialogContent>
        </Dialog>)
  }

  function UserDelete({userId}: {userId: number})
  {  
    const handleDelete = async () => {
      try {
          const dataSend = {"auth_id": userId}
          const response = await fetch("/delete-user", {
            method: "DELETE",
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(dataSend),
          });
    
          const data_resp = await response.json();
          if (data_resp.error) {
            console.log(data_resp.error);
            return;
          }
          getUsers();
        } 
        catch (error) {
          return ("Error:" + error);
        }
    };

    return (
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleDelete}
            >
              Delete
            </Button>
          )
  }

  

  return (
    <Card>
      <CardHeader>
        <CardTitle>Users</CardTitle>
        <CardDescription>Manage user accounts and their role-based permissions</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableCaption>A list of all registered users in the system</TableCaption>
          <TableHeader>
            <TableRow>
              <TableHead>User ID</TableHead>
              <TableHead>Username</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Role</TableHead>
              {/* <TableHead>Status</TableHead> */}
              <TableHead>Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.auth_id}>
                <TableCell className="font-mono text-sm">{user.auth_id}</TableCell>
                <TableCell className="font-medium">{user.username}</TableCell>
                <TableCell>
                  <Badge variant={user.role === "admin" ? "default" : "outline"}>{user.email}</Badge>
                </TableCell>
                <TableCell>
                  <Badge variant={user.role === "admin" ? "default" : "outline"}>{user.role}</Badge>
                </TableCell>
                {/* <TableCell>
                  <Badge variant={user.status === "active" ? "default" : "secondary"}>{user.status}</Badge>
                </TableCell> */}
                <TableCell>
                <div className="flex gap-2">
                  {user.auth_id !== currentUserAuthId && (
                    <>
                      <UserEdit userId={user.auth_id}/>
                      <UserDelete userId={user.auth_id}/>
                    </>
                  )}
                </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
