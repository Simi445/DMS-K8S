export type User = {
  auth_id: number;
  username: string;
  email: string;
  role: string;
};

export type Device = {
  device_id: number,
  auth_id: number;
  name: string;
  status: string;
  maxConsumption: number;
};

export type Consumption = {
  device_id: number;
  auth_id: number;
  consumption: string;
};

export type JWTPayload = {
    auth_id?: number;
    username?: string;
    exp?: number;
  };