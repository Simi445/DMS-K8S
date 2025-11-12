import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "./ui/form"
import { Input } from "./ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"
import { ConsumptionChart } from "./ui/consumption-chart"

import type { Device } from "@/lib/types"
import { useEffect, useState } from "react"
import DatePicker from "react-datepicker"
import "react-datepicker/dist/react-datepicker.css"

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
    const [selectedDate, setSelectedDate] = useState<Date>(new Date())
    const [chartData, setChartData] = useState<{hour: number, consumption: number}[]>([])
    const [chartType, setChartType] = useState<'line' | 'bar'>('line')
    const [showChartModal, setShowChartModal] = useState(false)

        const getDevicesById = async () => {
                const user = _users.find((u) => u.username === username);
                if (!user || !user.auth_id) {
                    console.log('User not found or auth_id missing:', user);
                    setDevicesById([]);
                    return;
                }
                const userId = user.auth_id;

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

    useEffect(() => {
        fetchChartData();
    }, [selectedDate, username, _users]);

    const fetchChartData = async () => {
        const user = _users.find((u) => u.username === username);
        if (!user || !user.auth_id) {
            console.log('User not found or auth_id missing:', user);
            setChartData([]);
            return;
        }

        const dateStr = selectedDate.toISOString().split('T')[0]; 

        try {
            const response = await fetch(`/consumptions?user_id=${user.auth_id}&date=${dateStr}`, {
                method: "GET",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${localStorage.getItem('token')}`
                }
            });
            if (!response.ok) {
                console.error("Failed to fetch chart data:", response.status, response.statusText);
                setChartData([]);
                return;
            }
            const data = await response.json();
            
            const hourlyConsumption: { [hour: number]: number[] } = {};
            
            data?.consumptions?.forEach((consumption: any) => {
                const timestamp = new Date(consumption.timestamp);
                const hour = timestamp.getHours();
                const consumptionValue = parseFloat(consumption.consumption);
                
                if (!hourlyConsumption[hour]) {
                    hourlyConsumption[hour] = [];
                }
                hourlyConsumption[hour].push(consumptionValue);
            });
            
            // Calculate average consumption per hour
            const hourlyData = [];
            for (let hour = 0; hour < 24; hour++) {
                const consumptions = hourlyConsumption[hour] || [];
                const averageConsumption = consumptions.length > 0 
                    ? consumptions.reduce((sum, val) => sum + val, 0) / consumptions.length 
                    : 0;
                
                hourlyData.push({
                    hour,
                    consumption: averageConsumption
                });
            }
            
            setChartData(hourlyData);
        } catch (error) {
            console.error("Error fetching chart data:", error);
            setChartData([]);
        }
    };


    function DeviceEdit({ deviceId }: { deviceId: number }) {
        const currentDevice = devices.find((device) => device.device_id === deviceId);

        const handleDialogOpen = () => {
            if (currentDevice) {
                const deviceDataMap = {
                    name: currentDevice.name,
                    maxConsumption: currentDevice.maxConsumption.toString(),
                    status: currentDevice.status,
                    assignedTo: currentDevice.auth_id?.toString() ?? 'no_user'
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
                                                <SelectItem key={user.auth_id} value={user.auth_id.toString()}>
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
        <>
        <Card>
            <CardHeader>
                <CardTitle>Devices</CardTitle>
                <CardDescription>Manage all devices with their consumption limits and assignments</CardDescription>
                <div className="flex gap-2 mt-4">
                    <Button onClick={() => setShowChartModal(true)} variant="outline">
                        View Consumption Chart
                    </Button>
                </div>
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
                                <TableCell className="text-muted-foreground">{(_users.find(user => String(user.auth_id) === String(device.auth_id))?.username) || "Unassigned"}</TableCell>
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
                                <TableCell className="text-muted-foreground">{(_users.find(user => String(user.auth_id) === String(device.auth_id))?.username) || "Unassigned"}</TableCell>
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

        <Dialog open={showChartModal} onOpenChange={setShowChartModal}>
            <DialogContent className="max-w-4xl">
                <DialogHeader>
                    <DialogTitle>Energy Consumption Chart</DialogTitle>
                    <DialogDescription>
                        View your historical energy consumption for a selected day
                    </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                    <div className="flex gap-4 items-center">
                        <div>
                            <label className="text-sm font-medium">Select Date:</label>
                            <DatePicker
                                selected={selectedDate}
                                onChange={(date) => setSelectedDate(date || new Date())}
                                dateFormat="yyyy-MM-dd"
                                className="ml-2 p-2 border rounded"
                            />
                        </div>
                        <div>
                            <label className="text-sm font-medium">Chart Type:</label>
                            <Select value={chartType} onValueChange={(value: 'line' | 'bar') => setChartType(value)}>
                                <SelectTrigger className="ml-2 w-32">
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="line">Line Chart</SelectItem>
                                    <SelectItem value="bar">Bar Chart</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                        <Button onClick={fetchChartData} variant="outline">
                            Load Chart
                        </Button>
                    </div>
                    {chartData.length > 0 && (
                        <div className="w-full">
                            <ConsumptionChart data={chartData} chartType={chartType} />
                        </div>
                    )}
                    {chartData.length === 0 && (
                        <div className="text-center text-muted-foreground">
                            No consumption data available for the selected date
                        </div>
                    )}
                </div>
            </DialogContent>
        </Dialog>
        </>
    )
}
