import { DeviceTable } from "@/components/device-table"
import { UserTable } from "@/components/user-table"
import { ChatWindow } from "@/components/chat-window"
import { AdminChat } from "@/components/admin-chat"
import { OverconsumptionAlertListener } from "@/components/overconsumption-alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Button } from "@/components/ui/button"
import { useEffect, useState } from "react"
import type { User as UserType, Device as DeviceType } from "@/lib/types"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { useForm } from "react-hook-form"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"



type HomeProps = {
  handleLogout: () => void;
  role:string;
  username:string;
  currentUserAuthId: number | null;
}

export default function Home({handleLogout, role, username, currentUserAuthId}: HomeProps) {

  function Register() {
    const deviceform = useForm({
      defaultValues: {
      name: '',
      status: '',
      maxConsumption: '',
      assignedTo: '',
    }
  });

  const userForm = useForm({
      defaultValues: {
      username: '',
      email: '',
      role: '',
      password: '',
    }
  });


  const [deviceOpen, setDeviceOpen] = useState(true)
  const [error, setError] = useState('');
  const [users, setUsers] = useState<UserType[]>([])
  const [devices, setDevices] = useState<DeviceType[]>([])
  const [showChat, setShowChat] = useState(false)

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



  const getUsers = async () =>
            {
              const response = await fetch("/users", {
              method: "GET",
              headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem('token')}`
              }
            });
              try {
                const data = await response.json();
                setUsers(data['users'])
              } 
              catch (error) {
                console.log("Error:" + error);
              }
            }

  const getDevices = async () =>
            {
              const response = await fetch("/devices", {
              method: "GET",
              headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem('token')}` 
              }
            });
              try {
                const data = await response.json();
                setDevices(data['devices'])
              } 
              catch (error) {
                console.log("Error:" + error);
              }
            }

  useEffect(() => {
    getUsers();
    getDevices();
  }, []);


 


  function AddPopUp()
  {
    const onSubmitUser = async (data: any) => {
      const dataToSend = data
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
            userForm.reset();
            getUsers();
          }
        } 
        catch (error) {
          return ("Error:" + error);
        }
    };

    const onSubmitDevice = async (data:any) =>
      {
      const dataToSend = {
        name: data.name,
        status: data.status,
        maxConsumption: data.maxConsumption,
        assignedTo: data.assignedTo,
      }
      
      try {
        const response = await fetch('/add-device', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json',
            "Authorization": `Bearer ${localStorage.getItem('token')}`
           },
          body: JSON.stringify(dataToSend),
        })
        const result = await response.json()
        if (!response.ok) {
          setError(result.error || `Server error: ${response.status}`)
        } else {
          deviceform.reset();
          getDevices();
        }
      } catch (err: any) {
        return ("Error:" + error);
      }
    }
    return (role === "admin" && <Dialog>
          <DialogTrigger asChild>
            <Button variant="outline" size="sm" className="w-full">
              {deviceOpen ? <p>Add Device</p>: <p>Add User</p> }
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Enter {deviceOpen ? 'device' : 'user'} data:</DialogTitle>
              <DialogDescription>
                Fill in the form below to add a new {deviceOpen ? 'device' : 'user'}.
              </DialogDescription>
            </DialogHeader>
            
            {!deviceOpen ? (
              <Form {...userForm}>
                <form onSubmit={userForm.handleSubmit(onSubmitUser)} className="space-y-4">
                  <FormField
                    control={userForm.control}
                    name="username"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Username</FormLabel>
                        <FormControl>
                          <Input placeholder="Enter username" {...field} />
                        </FormControl>
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
                            <SelectItem value="admin">Admin</SelectItem>
                            <SelectItem value="user">User</SelectItem>
                          </SelectContent>
                        </Select>
                      </FormItem>
                    )}
                  />
                  
                  
                <FormField
                control={userForm.control}
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
                  
                  <div className="flex justify-end space-x-2 pt-4">
                    <Button type="submit">Add User</Button>
                  </div>
                </form>
              </Form>
            ) : (<Form {...deviceform}>
                <form onSubmit={deviceform.handleSubmit(onSubmitDevice)} className="space-y-4">
                  <FormField
                    control={deviceform.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Name</FormLabel>
                        <FormControl>
                          <Input placeholder="Enter name" {...field} />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={deviceform.control}
                    name="status"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Status</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select a status" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="active">Active</SelectItem>
                            <SelectItem value="inactive">Inactive</SelectItem>
                          </SelectContent>
                        </Select>
                      </FormItem>
                    )}
                    />
                    
                    <FormField
                    control={deviceform.control}
                    name="maxConsumption"
                    render={({ field }) => (
                      <FormItem>
                      <FormLabel>Max Consumption</FormLabel>
                      <FormControl>
                        <Input
                        type="number"
                        placeholder="0"
                        min={0}
                        max={5000}
                        {...field}
                        />
                      </FormControl>
                      </FormItem>
                    )}
                    />
                    
                    <FormField
                    control={deviceform.control}
                    name="assignedTo"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Assigned To</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select owner" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {users.map((user) => (
                            <SelectItem key={user.auth_id} value={`${user.auth_id}`}>{user.username}</SelectItem>
                        ))}
                          </SelectContent>
                        </Select>
                      </FormItem>
                    )}
                  />
                  
                  <div className="flex justify-end space-x-2 pt-4">
                    <Button type="submit">Add Device</Button>
                  </div>
                </form>
              </Form>)}
          </DialogContent>
        </Dialog>)
  }

  
  return (
    <div className="min-h-screen relative">
      {/* Overconsumption Alert Listener */}
      {currentUserAuthId && (
        <OverconsumptionAlertListener userId={currentUserAuthId.toString()} />
      )}
      
      <Button 
        onClick={handleLogout}
        variant="outline"
        className="fixed top-0 right-0 m-4 z-10"
      >
        Logout
      </Button>

      <main className="min-h-screen flex flex-col items-center justify-center p-6 md:p-8 pt-16 md:pt-20">
        <div className="w-full max-w-full space-y-8">
        <div className="text-center space-y-4">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-balance">
        Device & User Management1
          </h1>
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded inline-block">
          {error}
            </div>
          )}
        </div>
        <Tabs defaultValue="devices" className="w-full" onValueChange={(val: any) => setDeviceOpen(val === 'devices')}>
          {(role === "admin") ? (<TabsList className="grid w-full max-w-md mx-auto grid-cols-3">
          <TabsTrigger value="devices">Devices</TabsTrigger>
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="chats">Chats</TabsTrigger>
          </TabsList>) : null}

          <TabsContent value="devices" className="mt-8">
  <DeviceTable deviceForm={deviceform} devices={devices} _users={users} _setDevices={setDevices} getDevices={getDevices} username={username} role={role}/>
          </TabsContent>

          <TabsContent value="users" className="mt-8">
        <UserTable users={users} setUsers={setUsers} getUsers={getUsers} userForm={userForm} currentUserAuthId={currentUserAuthId}/>
          </TabsContent>

          <TabsContent value="chats" className="mt-8">
            {currentUserAuthId && (
              <AdminChat adminId={currentUserAuthId.toString()} adminName={username} />
            )}
          </TabsContent>
        </Tabs>
        
        <AddPopUp/>
        
        {/* Chat Button - visible for non-admin users only */}
        {role !== "admin" && !showChat && (
          <Button 
            onClick={() => setShowChat(true)}
            className="fixed bottom-6 right-6 rounded-full w-14 h-14 shadow-lg"
            size="icon"
          >
            💬
          </Button>
        )}
        
        {/* Chat Window - only for non-admin users */}
        {role !== "admin" && showChat && currentUserAuthId && (
          <ChatWindow 
            userId={currentUserAuthId.toString()} 
            userName={username}
            onClose={() => setShowChat(false)}
          />
        )}
        
        </div>
      </main>
    </div>
  )
}

return (<Register/>)
}
