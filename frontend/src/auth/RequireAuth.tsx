import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useAuth } from './AuthContext';


export const RequireAuth: React.FC<{ children: React.ReactNode; reason?: string }>
= ({ children, reason }) => {
const { state, authenticate } = useAuth();
if (state.isAuthenticated) return <>{children}</>;
return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 }}>
        <Text style={{ fontSize: 18, marginBottom: 12 }}>Originals locked</Text>
            <Pressable
                onPress={() => authenticate({ reason })}
                style={{ paddingHorizontal: 16, paddingVertical: 12, backgroundColor: '#111', borderRadius: 10 }}
                >
            <Text style={{ color: 'white', fontWeight: '600' }}>Unlock</Text>
            </Pressable>
        <Text style={{ marginTop: 12, color: '#666' }}>Biometric or PIN</Text>
    </View>);
};