import React, { useEffect, useState } from 'react';
import { View, Text, Pressable, TextInput, Alert } from 'react-native';
import { useAuth } from '../auth/AuthContext';


export const LockScreen: React.FC = () => {
const { authenticate, setPin, hasPin } = useAuth();
const [pin, setPinState] = useState('');
const [hasExistingPin, setHasExistingPin] = useState<boolean | null>(null);


useEffect(() => {
hasPin().then(setHasExistingPin).catch(() => setHasExistingPin(false));
}, [hasPin]);


return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 }}>
        <Text style={{ fontSize: 22, fontWeight: '700', marginBottom: 16 }}>Privacy lock</Text>
        <Pressable onPress={() => authenticate({ reason: 'Unlock Originals' })} style={{ backgroundColor: '#111', paddingHorizontal: 16, paddingVertical: 12, borderRadius: 10 }}>
            <Text style={{ color: 'white' }}>Use biometric</Text>
        </Pressable>
        <View style={{ height: 16 }} />
            <TextInput
                value={pin}
                onChangeText={setPinState}
                placeholder={hasExistingPin ? 'Update PIN' : 'Set PIN'}
                secureTextEntry
                keyboardType='number-pad'
                style={{ width: '80%', borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 10 }}
        />
        <View style={{ height: 8 }} />
        <Pressable
            onPress={async () => {
                try {
                    await setPin(pin);
                    Alert.alert('PIN saved');
                    setPinState('');
                } catch (e: any) {
                    Alert.alert('Error', e.message || 'Failed to save PIN');
                }}
            }
            style={{ backgroundColor: '#eee', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8 }}
            >
            <Text>Save PIN</Text>
        </Pressable>
    </View>
);};