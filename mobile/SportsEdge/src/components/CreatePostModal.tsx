/**
 * Create Post Modal Component
 */
import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  TextInput,
  TouchableOpacity,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/Ionicons';

import { RootState } from '../store';
import { apiClient } from '../services';
import { useOfflineAnalytics } from '../hooks';

interface CreatePostModalProps {
  visible: boolean;
  onClose: () => void;
  onPostCreated: (post: any) => void;
}

const CreatePostModal: React.FC<CreatePostModalProps> = ({
  visible,
  onClose,
  onPostCreated,
}) => {
  const theme = useSelector((state: RootState) => state.userPreferences.theme);
  const { trackUserAction } = useOfflineAnalytics();

  const [postType, setPostType] = useState<'discussion' | 'analysis' | 'bet_share'>('discussion');
  const [content, setContent] = useState('');
  const [tags, setTags] = useState<string[]>([]);
  const [currentTag, setCurrentTag] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isDark = theme.theme === 'dark' || 
    (theme.theme === 'auto' && new Date().getHours() > 18);

  const colors = {
    background: isDark ? '#0F172A' : '#FFFFFF',
    surface: isDark ? '#1E293B' : '#F8FAFC',
    text: isDark ? '#F1F5F9' : '#1E293B',
    textSecondary: isDark ? '#94A3B8' : '#64748B',
    border: isDark ? '#334155' : '#E2E8F0',
    accent: theme.accentColor,
    success: '#10B981',
    warning: '#F59E0B',
    error: '#EF4444',
  };

  const styles = StyleSheet.create({
    overlay: {
      flex: 1,
      backgroundColor: 'rgba(0,0,0,0.5)',
      justifyContent: 'flex-end',
    },
    container: {
      backgroundColor: colors.background,
      borderTopLeftRadius: 20,
      borderTopRightRadius: 20,
      maxHeight: '90%',
    },
    header: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingHorizontal: 20,
      paddingVertical: 16,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    headerTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: colors.text,
    },
    headerButton: {
      paddingHorizontal: 16,
      paddingVertical: 8,
      borderRadius: 8,
    },
    cancelButton: {
      backgroundColor: 'transparent',
    },
    submitButton: {
      backgroundColor: colors.accent,
    },
    disabledButton: {
      opacity: 0.5,
    },
    headerButtonText: {
      fontSize: 16,
      fontWeight: '600',
    },
    cancelButtonText: {
      color: colors.textSecondary,
    },
    submitButtonText: {
      color: '#FFFFFF',
    },
    content: {
      padding: 20,
    },
    typeSelector: {
      marginBottom: 20,
    },
    typeSelectorTitle: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
      marginBottom: 12,
    },
    typeOptions: {
      flexDirection: 'row',
      gap: 12,
    },
    typeOption: {
      flex: 1,
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 12,
      paddingHorizontal: 16,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: colors.border,
      backgroundColor: colors.surface,
    },
    selectedTypeOption: {
      backgroundColor: colors.accent + '20',
      borderColor: colors.accent,
    },
    typeOptionIcon: {
      marginRight: 8,
    },
    typeOptionText: {
      fontSize: 14,
      fontWeight: '500',
      color: colors.textSecondary,
    },
    selectedTypeOptionText: {
      color: colors.accent,
    },
    contentInput: {
      borderWidth: 1,
      borderColor: colors.border,
      borderRadius: 12,
      padding: 16,
      fontSize: 16,
      color: colors.text,
      backgroundColor: colors.surface,
      textAlignVertical: 'top',
      minHeight: 120,
      maxHeight: 200,
    },
    contentLabel: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
      marginBottom: 8,
    },
    characterCount: {
      fontSize: 12,
      color: colors.textSecondary,
      textAlign: 'right',
      marginTop: 4,
    },
    overLimit: {
      color: colors.error,
    },
    tagsSection: {
      marginTop: 20,
    },
    tagsTitle: {
      fontSize: 16,
      fontWeight: '600',
      color: colors.text,
      marginBottom: 8,
    },
    tagInputContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 12,
    },
    tagInput: {
      flex: 1,
      borderWidth: 1,
      borderColor: colors.border,
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 8,
      fontSize: 14,
      color: colors.text,
      backgroundColor: colors.surface,
    },
    addTagButton: {
      backgroundColor: colors.accent,
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 8,
      marginLeft: 8,
    },
    addTagButtonText: {
      color: '#FFFFFF',
      fontSize: 14,
      fontWeight: '600',
    },
    tagsList: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 8,
    },
    tag: {
      backgroundColor: colors.accent + '20',
      borderRadius: 16,
      paddingHorizontal: 12,
      paddingVertical: 6,
      flexDirection: 'row',
      alignItems: 'center',
    },
    tagText: {
      fontSize: 12,
      color: colors.accent,
      fontWeight: '500',
    },
    removeTagButton: {
      marginLeft: 4,
    },
    suggestedTags: {
      marginTop: 12,
    },
    suggestedTagsTitle: {
      fontSize: 14,
      color: colors.textSecondary,
      marginBottom: 8,
    },
    suggestedTagsList: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 8,
    },
    suggestedTag: {
      backgroundColor: colors.surface,
      borderWidth: 1,
      borderColor: colors.border,
      borderRadius: 16,
      paddingHorizontal: 12,
      paddingVertical: 6,
    },
    suggestedTagText: {
      fontSize: 12,
      color: colors.textSecondary,
    },
  });

  const postTypes = [
    { id: 'discussion', label: 'Discussion', icon: 'chatbubbles' },
    { id: 'analysis', label: 'Analysis', icon: 'analytics' },
    { id: 'bet_share', label: 'Bet Share', icon: 'flash' },
  ];

  const suggestedTags = ['NBA', 'NFL', 'MLB', 'NHL', 'ValueBets', 'LiveBetting', 'Parlays', 'Props'];

  const MAX_CONTENT_LENGTH = 500;
  const MAX_TAGS = 5;

  const handleClose = useCallback(() => {
    if (content.trim() || tags.length > 0) {
      Alert.alert(
        'Discard Post?',
        'Your post will be lost if you close now.',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Discard', style: 'destructive', onPress: onClose },
        ]
      );
    } else {
      onClose();
    }
  }, [content, tags, onClose]);

  const handleAddTag = useCallback(() => {
    const tag = currentTag.trim().replace('#', '');
    if (tag && !tags.includes(tag) && tags.length < MAX_TAGS) {
      setTags(prev => [...prev, tag]);
      setCurrentTag('');
    }
  }, [currentTag, tags]);

  const handleRemoveTag = useCallback((tagToRemove: string) => {
    setTags(prev => prev.filter(tag => tag !== tagToRemove));
  }, []);

  const handleAddSuggestedTag = useCallback((tag: string) => {
    if (!tags.includes(tag) && tags.length < MAX_TAGS) {
      setTags(prev => [...prev, tag]);
    }
  }, [tags]);

  const handleSubmit = useCallback(async () => {
    if (!content.trim()) {
      Alert.alert('Error', 'Please enter some content for your post.');
      return;
    }

    if (content.length > MAX_CONTENT_LENGTH) {
      Alert.alert('Error', `Post content cannot exceed ${MAX_CONTENT_LENGTH} characters.`);
      return;
    }

    try {
      setIsSubmitting(true);

      const postData = {
        type: postType,
        content: content.trim(),
        tags: tags,
      };

      const response = await apiClient.post('/social/posts', postData);
      
      await trackUserAction('create_post', {
        type: postType,
        content_length: content.length,
        tags_count: tags.length,
      });

      onPostCreated(response.data);
      
      // Reset form
      setContent('');
      setTags([]);
      setCurrentTag('');
      setPostType('discussion');
      
      Alert.alert('Success', 'Your post has been shared!');
    } catch (error: any) {
      console.error('Error creating post:', error);
      Alert.alert('Error', error.message || 'Failed to create post. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [content, postType, tags, onPostCreated, trackUserAction]);

  const canSubmit = content.trim().length > 0 && 
                   content.length <= MAX_CONTENT_LENGTH && 
                   !isSubmitting;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      transparent
      onRequestClose={handleClose}
    >
      <KeyboardAvoidingView 
        style={styles.overlay}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <View style={styles.container}>
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity 
              style={[styles.headerButton, styles.cancelButton]}
              onPress={handleClose}
            >
              <Text style={[styles.headerButtonText, styles.cancelButtonText]}>
                Cancel
              </Text>
            </TouchableOpacity>
            
            <Text style={styles.headerTitle}>Create Post</Text>
            
            <TouchableOpacity 
              style={[
                styles.headerButton, 
                styles.submitButton,
                !canSubmit && styles.disabledButton
              ]}
              onPress={handleSubmit}
              disabled={!canSubmit}
            >
              <Text style={[styles.headerButtonText, styles.submitButtonText]}>
                {isSubmitting ? 'Posting...' : 'Post'}
              </Text>
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            {/* Post Type Selector */}
            <View style={styles.typeSelector}>
              <Text style={styles.typeSelectorTitle}>Post Type</Text>
              <View style={styles.typeOptions}>
                {postTypes.map((type) => (
                  <TouchableOpacity
                    key={type.id}
                    style={[
                      styles.typeOption,
                      postType === type.id && styles.selectedTypeOption,
                    ]}
                    onPress={() => setPostType(type.id as any)}
                  >
                    <Icon 
                      name={type.icon} 
                      size={16} 
                      color={postType === type.id ? colors.accent : colors.textSecondary}
                      style={styles.typeOptionIcon}
                    />
                    <Text style={[
                      styles.typeOptionText,
                      postType === type.id && styles.selectedTypeOptionText,
                    ]}>
                      {type.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            {/* Content Input */}
            <View>
              <Text style={styles.contentLabel}>What's on your mind?</Text>
              <TextInput
                style={styles.contentInput}
                value={content}
                onChangeText={setContent}
                placeholder={`Share your ${postType === 'bet_share' ? 'bet' : postType}...`}
                placeholderTextColor={colors.textSecondary}
                multiline
                maxLength={MAX_CONTENT_LENGTH}
              />
              <Text style={[
                styles.characterCount,
                content.length > MAX_CONTENT_LENGTH * 0.9 && styles.overLimit,
              ]}>
                {content.length}/{MAX_CONTENT_LENGTH}
              </Text>
            </View>

            {/* Tags Section */}
            <View style={styles.tagsSection}>
              <Text style={styles.tagsTitle}>Tags (Optional)</Text>
              
              <View style={styles.tagInputContainer}>
                <TextInput
                  style={styles.tagInput}
                  value={currentTag}
                  onChangeText={setCurrentTag}
                  placeholder="Add a tag..."
                  placeholderTextColor={colors.textSecondary}
                  onSubmitEditing={handleAddTag}
                  maxLength={20}
                />
                <TouchableOpacity 
                  style={styles.addTagButton}
                  onPress={handleAddTag}
                  disabled={!currentTag.trim() || tags.length >= MAX_TAGS}
                >
                  <Text style={styles.addTagButtonText}>Add</Text>
                </TouchableOpacity>
              </View>

              {tags.length > 0 && (
                <View style={styles.tagsList}>
                  {tags.map((tag, index) => (
                    <View key={index} style={styles.tag}>
                      <Text style={styles.tagText}>#{tag}</Text>
                      <TouchableOpacity 
                        style={styles.removeTagButton}
                        onPress={() => handleRemoveTag(tag)}
                      >
                        <Icon name="close" size={12} color={colors.accent} />
                      </TouchableOpacity>
                    </View>
                  ))}
                </View>
              )}

              {tags.length < MAX_TAGS && (
                <View style={styles.suggestedTags}>
                  <Text style={styles.suggestedTagsTitle}>Suggested Tags:</Text>
                  <View style={styles.suggestedTagsList}>
                    {suggestedTags
                      .filter(tag => !tags.includes(tag))
                      .slice(0, 6)
                      .map((tag, index) => (
                        <TouchableOpacity
                          key={index}
                          style={styles.suggestedTag}
                          onPress={() => handleAddSuggestedTag(tag)}
                        >
                          <Text style={styles.suggestedTagText}>#{tag}</Text>
                        </TouchableOpacity>
                      ))}
                  </View>
                </View>
              )}
            </View>
          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

export default CreatePostModal;