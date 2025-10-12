import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "./ui/form"
import { Input } from "./ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"


import type { Device } from "@/lib/types"
import { useEffect, useState } from "react"

type DeviceTableProps = {
    deviceForm: any,
    _users: any[],
    devices: Device[],
    _setDevices?: (d: Device[]) => void,
    getDevices: () => void,
    username: string,
    role: string
}

export function DeviceTable({ deviceForm, _users, devices, _setDevices, getDevices, username, role}: DeviceTableProps) {

    const [devicesById, setDevicesById] = useState<Device[]>([])

        const getDevicesById = async () => {
                const user = _users.find((u) => u.username === username);
                const userId = user.user_id;

                try {
                        const response = await fetch(`/devices/${userId}`, {
                        method: "GET",
                        headers: {
                            "Content-Type": "application/json",
                            "Authorization": `Bearer ${localStorage.getItem('token')}`
                        }
                        });
                        if (!response.ok) {
                                console.error("Failed to fetch devices:", response.status, response.statusText);
                                setDevicesById([]);
                                return;
                        }

                        const data = await response.json();
                        setDevicesById(data?.devices || []);
                } catch (error) {
                        setDevicesById([]);
                }
        };
    useEffect(() => {
        getDevicesById();
    }, [username, _users]);


    function DeviceEdit({ deviceId }: { deviceId: number }) {
        const currentDevice = devices.find((device) => device.device_id === deviceId);

        const handleDialogOpen = () => {
            if (currentDevice) {
                const deviceDataMap = {
                    name: currentDevice.name,
                    maxConsumption: currentDevice.maxConsumption.toString(),
                    status: currentDevice.status,
                    assignedTo: currentDevice.user_id?.toString() ?? 'no_user'
                };


                for (const [key, value] of Object.entries(deviceDataMap)) {
                    deviceForm.setValue(key, value);
                }
            }
        };

        

        const onSubmit = async (data: any) => {
            try {
                const dataSend = {"device_id": deviceId, ...data}
                const response = await fetch("/edit-device", {
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
                getDevices();
              } 
              catch (error) {
                console.error("Error:", error);
              }
        };

        return (<Dialog>
            <DialogTrigger asChild>
                {role === "admin" && (<Button
                    variant="outline"
                    size="sm"
                    onClick={handleDialogOpen}
                >
                    Edit
                </Button>)}
            </DialogTrigger>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle>Edit data:</DialogTitle>
                    <DialogDescription>
                        Fill in the form below to edit user data.
                    </DialogDescription>
                </DialogHeader>
                <Form {...deviceForm}>
                    <form onSubmit={deviceForm.handleSubmit(onSubmit)} className="space-y-4">
                        <FormField
                            control={deviceForm.control}
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
                            control={deviceForm.control}
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
                            control={deviceForm.control}
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
                            control={deviceForm.control}
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
                                            <SelectItem value="no_user">Unassigned</SelectItem>
                                            {_users.map((user) => (
                                                <SelectItem key={user.user_id} value={user.user_id.toString()}>
                                                    {user.username}
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </FormItem>
                            )}
                        />

                        <div className="flex justify-end space-x-2 pt-4">
                            <Button type="submit">Edit Device</Button>
                        </div>
                    </form>
                </Form>
            </DialogContent>
        </Dialog>)
    }

function DeviceDelete({deviceId}: {deviceId: number})
  {  
    const handleDelete = async () => {
      try {
          const dataSend = {"device_id": deviceId}
          const response = await fetch("/delete-device", {
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
          getDevices();
        } 
        catch (error) {
          return ("Error:" + error);
        }
    };

    return (
        <>
            {role === "admin" && (
                <Button 
                    variant="outline" 
                    size="sm"
                    onClick={handleDelete}
                >
                    Delete
                </Button>
            )}
        </>
    );
  }
    return (
        <Card>
            <CardHeader>
                <CardTitle>Devices</CardTitle>
                <CardDescription>Manage all devices with their consumption limits and assignments</CardDescription>
            </CardHeader>
            <CardContent>
                <Table>
                    <TableCaption>A list of all registered devices in the system</TableCaption>
                    <TableHeader>
                        <TableRow>
                            <TableHead>Device ID</TableHead>
                            <TableHead>Name</TableHead>
                            <TableHead>Max Consumption (W)</TableHead>
                            <TableHead>Status</TableHead>
                            <TableHead>Assigned To</TableHead>
                            <TableHead>Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    {role =="admin" ? 
                    (<TableBody>
                        {devices.map((device) => (
                            <TableRow key={device.device_id}>
                                <TableCell className="font-mono text-sm">{device.device_id}</TableCell>
                                <TableCell className="font-medium">{device.name}</TableCell>
                                <TableCell>{device.maxConsumption}</TableCell>
                                <TableCell>
                                    <Badge variant={device.status === "active" ? "default" : "secondary"}>{device.status}</Badge>
                                </TableCell>
                                <TableCell className="text-muted-foreground">{(_users.find(user => String(user.user_id) === String(device.user_id))?.username) || "Unassigned"}</TableCell>
                                <TableCell>
                                    <div className="flex gap-2">
                                        <DeviceEdit deviceId={device.device_id} />
                                        <DeviceDelete deviceId={device.device_id} />
                                    </div>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>) :
                    (<TableBody>
                        {devicesById.map((device) => (
                            <TableRow key={device.device_id}>
                                <TableCell className="font-mono text-sm">{device.device_id}</TableCell>
                                <TableCell className="font-medium">{device.name}</TableCell>
                                <TableCell>{device.maxConsumption}</TableCell>
                                <TableCell>
                                    <Badge variant={device.status === "active" ? "default" : "secondary"}>{device.status}</Badge>
                                </TableCell>
                                <TableCell className="text-muted-foreground">{(_users.find(user => String(user.user_id) === String(device.user_id))?.username) || "Unassigned"}</TableCell>
                                <TableCell>
                                    <div className="flex gap-2">
                                        <DeviceEdit deviceId={device.device_id} />
                                        <DeviceDelete deviceId={device.device_id} />
                                    </div>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>)
                    }
                </Table>
            </CardContent>
        </Card>
    )
}
