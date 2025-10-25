import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/utils/api';
import { Plant } from '@/components/plants/PlantsOverview';
import { Device } from '@/types/device';

export const usePlantsData = (userType = 'demo') => {
  // Fetch plants
  const { data: rawPlants = [], isLoading: plantsLoading, error: plantsError } = useQuery({
    queryKey: ['plants', userType],
    queryFn: () => apiClient.getPlants(userType),
    staleTime: 5 * 60 * 1000,
  });

  // Fetch devices
  const { data: rawDevices = [], isLoading: devicesLoading, error: devicesError } = useQuery({
    queryKey: ['devices', userType],
    queryFn: () => apiClient.getDevices(userType),
    staleTime: 5 * 60 * 1000,
  });

  // Map API plants to Plant interface
  const plants: Plant[] = rawPlants.map((p: any) => {
    const devicesForPlant = rawDevices.filter((d: any) => d.plant_id === p.plant_id);

    // Total current generation
    const totalGeneration = devicesForPlant.reduce((sum: number, d: any) => sum + (d.current_output || 0), 0);

    // Efficiency %
    const efficiency = p.capacity ? ((totalGeneration / p.capacity) * 100).toFixed(2) : 0;

    // Determine plant status dynamically
    let status: Plant['status'] = 'online';
    if (devicesForPlant.every((d: any) => d.status === 'offline')) {
      status = 'offline';
    } else if (devicesForPlant.some((d: any) => d.status === 'fault' || d.status === 'warning')) {
      status = 'maintenance';
    }

    return {
      id: p.plant_id,
      name: p.plant_name,
      location: p.location,
      totalCapacity: p.capacity,
      currentGeneration: totalGeneration,
      efficiency: Number(efficiency),
      deviceCount: devicesForPlant.length,
      status,
      lastUpdate: p.updated_at ? new Date(p.updated_at) : new Date(),
    } as Plant;
  });

  // Map API devices to Device interface
  const devices: Device[] = rawDevices.map((d: any) => ({
    id: d.device_sn,
    name: d.inverter_model || d.device_sn,
    plantId: d.plant_id,
    type: d.type || 'inverter',
    status: d.status || 'online',
    currentOutput: d.current_output || 0,
    efficiency: d.efficiency_percent || 0,
  }));

  return {
    plants,
    devices,
    isLoading: plantsLoading || devicesLoading,
    error: plantsError || devicesError,
  };
};
