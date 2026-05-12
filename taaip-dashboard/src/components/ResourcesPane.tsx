import React from 'react';
import { BookOpen, FileText, Video, Download, ExternalLink, Shield, Users, TrendingUp } from 'lucide-react';

interface Resource {
  id: string;
  title: string;
  description: string;
  type: 'guide' | 'video' | 'download' | 'link';
  url: string;
  icon: React.ReactNode;
  category: string;
}

const RESOURCES: Resource[] = [
  {
    id: 'r1',
    title: '420T Quick Start Guide',
    description: 'Complete guide for Talent Acquisition Technicians',
    type: 'guide',
    url: '/docs/420t-quick-start.pdf',
    icon: <BookOpen className="w-5 h-5" />,
    category: 'Training'
  },
  {
    id: 'r2',
    title: 'Recruiting Operations Manual',
    description: 'SOPs and best practices for recruiting operations',
    type: 'download',
    url: '/docs/recruiting-ops-manual.pdf',
    icon: <FileText className="w-5 h-5" />,
    category: 'Documentation'
  },
  {
    id: 'r3',
    title: 'TAAIP Platform Training',
    description: 'Video tutorials on using the TAAIP platform',
    type: 'video',
    url: 'https://training.taaip.army.mil/videos',
    icon: <Video className="w-5 h-5" />,
    category: 'Training'
  },
  {
    id: 'r4',
    title: 'Mission Analysis Guide',
    description: 'M-IPOE framework and targeting principles',
    type: 'guide',
    url: '/docs/mission-analysis-guide.pdf',
    icon: <TrendingUp className="w-5 h-5" />,
    category: 'Operations'
  },
  {
    id: 'r5',
    title: 'Access Control Policy',
    description: 'User roles, permissions, and security guidelines',
    type: 'download',
    url: '/docs/access-control-policy.pdf',
    icon: <Shield className="w-5 h-5" />,
    category: 'Security'
  },
  {
    id: 'r6',
    title: 'Data Entry Templates',
    description: 'Excel and CSV templates for bulk data import',
    type: 'download',
    url: '/templates/data-entry-templates.zip',
    icon: <Download className="w-5 h-5" />,
    category: 'Tools'
  },
  {
    id: 'r7',
    title: 'Leadership Dashboard Guide',
    description: 'Using analytics for strategic decision making',
    type: 'guide',
    url: '/docs/leadership-guide.pdf',
    icon: <Users className="w-5 h-5" />,
    category: 'Leadership'
  },
  {
    id: 'r8',
    title: 'Army Recruiting Portal',
    description: 'External link to Army Recruiting resources',
    type: 'link',
    url: 'https://recruiting.army.mil',
    icon: <ExternalLink className="w-5 h-5" />,
    category: 'External'
  }
];

export const ResourcesPane: React.FC = () => {
  const categories = Array.from(new Set(RESOURCES.map(r => r.category)));

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'guide': return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'video': return 'bg-purple-100 text-purple-700 border-purple-300';
      case 'download': return 'bg-green-100 text-green-700 border-green-300';
      case 'link': return 'bg-orange-100 text-orange-700 border-orange-300';
      default: return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-md border-2 border-gray-200">
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white px-6 py-4 border-b-2 border-yellow-500 rounded-t-xl">
        <h2 className="text-xl font-bold uppercase tracking-wider flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-yellow-500" />
          Resources & Documentation
        </h2>
        <p className="text-sm text-gray-300 mt-1">Training materials, guides, and tools for talent acquisition</p>
      </div>

      <div className="p-6">
        {categories.map((category) => (
          <div key={category} className="mb-6 last:mb-0">
            <h3 className="text-sm font-bold text-gray-700 uppercase tracking-wide mb-3 border-l-4 border-yellow-600 pl-3">
              {category}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {RESOURCES.filter(r => r.category === category).map((resource) => (
                <a
                  key={resource.id}
                  href={resource.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`flex items-start gap-3 p-4 rounded-lg border-2 transition-all hover:shadow-lg hover:scale-102 ${getTypeColor(resource.type)}`}
                  title={`${resource.description} - Click to ${resource.type === 'link' ? 'visit' : 'download'}`}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {resource.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="font-semibold text-sm">{resource.title}</h4>
                      {resource.type === 'link' && (
                        <ExternalLink className="w-4 h-4 flex-shrink-0" />
                      )}
                    </div>
                    <p className="text-xs mt-1 opacity-80">{resource.description}</p>
                    <span className="inline-block mt-2 text-xs uppercase font-bold tracking-wider">
                      {resource.type}
                    </span>
                  </div>
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="bg-gray-50 px-6 py-4 border-t-2 border-gray-200 rounded-b-xl">
        <p className="text-xs text-gray-600">
          Need additional resources? Submit a request through the <span className="font-semibold text-blue-600">Help Desk</span>.
        </p>
      </div>
    </div>
  );
};
