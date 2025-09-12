import Image from 'next/image';
import Link from 'next/link';
import { StarIcon } from '@heroicons/react/24/solid';

interface CharacterCardProps {
  id: number;
  name: string;
  avatarUrl: string;
  shortDescription: string;
  tags: string[];
  ratingAvg: number;
  ratingCount: number;
  gemCostPerMessage?: number;
  nsfwFlags: boolean;
  lastActive: string;
}

export function CharacterCard({
  id,
  name,
  avatarUrl,
  shortDescription,
  tags,
  ratingAvg,
  ratingCount,
  gemCostPerMessage,
  nsfwFlags,
  lastActive,
}: CharacterCardProps) {
  return (
    <Link href={`/character/${id}`}>
      <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 cursor-pointer overflow-hidden group">
        <div className="relative h-48 w-full">
          <Image
            src={avatarUrl}
            alt={name}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-200"
          />
          {nsfwFlags && (
            <div className="absolute top-2 right-2 bg-red-500 text-white text-xs px-2 py-1 rounded">
              18+
            </div>
          )}
        </div>
        
        <div className="p-4">
          <h3 className="font-semibold text-lg text-gray-900 mb-1 truncate">
            {name}
          </h3>
          
          <p className="text-gray-600 text-sm mb-3 line-clamp-2">
            {shortDescription}
          </p>
          
          <div className="flex items-center mb-2">
            <StarIcon className="h-4 w-4 text-yellow-400 mr-1" />
            <span className="text-sm font-medium text-gray-900">{ratingAvg}</span>
            <span className="text-sm text-gray-500 ml-1">({ratingCount})</span>
          </div>
          
          {gemCostPerMessage && (
            <div className="text-sm text-purple-600 mb-2">
              💎 {gemCostPerMessage} gems per message
            </div>
          )}
          
          <div className="flex flex-wrap gap-1 mb-2">
            {tags.slice(0, 3).map((tag) => (
              <span
                key={tag}
                className="inline-block bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full"
              >
                {tag}
              </span>
            ))}
            {tags.length > 3 && (
              <span className="inline-block bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded-full">
                +{tags.length - 3}
              </span>
            )}
          </div>
          
          <div className="text-xs text-gray-500">
            Last active: {new Date(lastActive).toLocaleDateString()}
          </div>
        </div>
      </div>
    </Link>
  );
}